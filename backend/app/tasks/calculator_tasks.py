import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.tasks.celery_app import celery_app


from app.db.session import AsyncSessionLocal, engine

from app.modules.catalog.models import Product, ProductCategory, ProductProgressionRule
from app.modules.profiling.models import Household, Member
from app.modules.calculator.models import LifetimeSubscription
from app.core.config import settings
from app.core.settings_loader import load_settings


@celery_app.task(name="app.tasks.calculator_tasks.generate_projections")
def generate_projections(household_id: str):
    import asyncio

    async def _run():
        household_uuid = uuid.UUID(household_id)
        await engine.dispose()
        try:
            async with AsyncSessionLocal() as db:
                config = await load_settings(db, [
                    "dietary_multipliers",
                    "lifestyle_tag_multipliers",
                    "default_price_ceiling_pct",
                    "organic_consumption_multiplier",
                ])
                dietary_multipliers = config["dietary_multipliers"]
                lifestyle_multipliers = config["lifestyle_tag_multipliers"]
                ceiling_pct = Decimal(str(config["default_price_ceiling_pct"]["pct"]))
                organic_mult_rate = config["organic_consumption_multiplier"]["rate"]

                result = await db.execute(
                    select(Household)
                    .where(Household.id == household_uuid)
                    .options(selectinload(Household.members))
                )
                household = result.scalar_one_or_none()
                if not household:
                    return {"error": "Household not found", "household_id": household_id}

                result = await db.execute(select(ProductCategory))
                categories = list(result.scalars().all())

                result = await db.execute(
                    select(ProductProgressionRule).options(selectinload(ProductProgressionRule.specific_product))
                )
                all_rules = list(result.scalars().all())

                rules_by_category: dict[uuid.UUID, list[ProductProgressionRule]] = {}
                for rule in all_rules:
                    rules_by_category.setdefault(rule.category_id, []).append(rule)

                created = 0
                today = date.today()

                for member in household.members:
                    if not member.is_active:
                        continue

                    age_years = (today - member.date_of_birth).days / 365.25

                    for category in categories:
                        max_age = category.max_age_limit_years
                        if max_age and age_years >= max_age:
                            continue

                        end_age = min(max_age or settings.MAX_LIFETIME_YEARS, settings.MAX_LIFETIME_YEARS)

                        progression_rules = rules_by_category.get(category.id)
                        if progression_rules:
                            created += await _create_progression_subscriptions(
                                db, household.id, member, category, progression_rules, today, ceiling_pct
                            )
                        else:
                            created += await _create_simple_subscription(
                                db, household.id, member, category, today, age_years, end_age,
                                dietary_multipliers, lifestyle_multipliers, ceiling_pct, organic_mult_rate
                            )

                await db.commit()
                return {"household_id": household_id, "subscriptions_created": created}
        finally:
            await engine.dispose()

    return asyncio.run(_run())


async def _create_progression_subscriptions(db, household_id, member, category, rules, today, ceiling_pct):
    created = 0
    birth = member.date_of_birth

    for rule in sorted(rules, key=lambda r: r.start_age_months):
        start_age_yrs = rule.start_age_months / 12
        end_age_yrs = rule.end_age_months / 12

        start_date = birth + timedelta(days=int(start_age_yrs * 365.25))
        end_date = birth + timedelta(days=int(end_age_yrs * 365.25))

        if today > end_date:
            continue

        if today > start_date:
            start_date = today

        years_span = max((end_date - start_date).days / 365.25, 1)
        freq_days = _frequency_for_age_product(start_age_yrs)

        existing = await db.execute(
            select(LifetimeSubscription).where(
                LifetimeSubscription.household_id == household_id,
                LifetimeSubscription.member_id == member.id,
                LifetimeSubscription.product_id == rule.specific_product_id,
                LifetimeSubscription.status == "active",
            )
        )
        if existing.scalar_one_or_none():
            continue

        sub = LifetimeSubscription(
            household_id=household_id,
            member_id=member.id,
            product_id=rule.specific_product.id,
            quantity_per_delivery=1.0,
            frequency_days=freq_days,
            start_date=start_date,
            end_date=end_date,
            next_delivery_date=start_date,
            status="active",
            source="direct",
            locked_unit_price=rule.specific_product.unit_price_wholesale,
            price_ceiling_pct=ceiling_pct,
        )
        db.add(sub)
        created += 1

    return created


async def _create_simple_subscription(db, household_id, member, category, today, age_years, end_age, dietary_multipliers, lifestyle_multipliers, ceiling_pct, organic_mult_rate):
    result = await db.execute(
        select(Product).where(
            Product.category_id == category.id,
            Product.is_active == True,
        ).limit(1)
    )
    product = result.scalar_one_or_none()
    if not product or not category.avg_lifetime_consumption_per_year:
        return 0

    dietary_mult = dietary_multipliers.get(member.dietary_preference or "vegetarian", 1.0)

    lifestyle_mult = 1.0
    for tag in member.lifestyle_tags or []:
        lifestyle_mult *= lifestyle_multipliers.get(tag, 1.0)

    result = await db.execute(
        select(Household).where(Household.id == household_id)
    )
    household = result.scalar_one_or_none()
    organic_mult = organic_mult_rate if household and household.prefer_organic else 1.0

    yearly_qty = float(category.avg_lifetime_consumption_per_year) * dietary_mult * lifestyle_mult * organic_mult
    daily_qty = yearly_qty / 365

    freq_days = _determine_frequency(category.unit_type, daily_qty)
    qty_per_delivery = daily_qty * freq_days

    # end_date = member.date_of_birth + timedelta(days=int(end_age * 365.25))
    if category.max_age_limit_years:
        # If it's an age-specific product (like infant formula), keep the birth calculation
        end_date = member.date_of_birth + timedelta(days=int(category.max_age_limit_years * 365.25))
    else:
        # For lifetime staples (rice, sugar), project forward from TODAY
        end_date = today + timedelta(days=int(settings.MAX_LIFETIME_YEARS * 365.25))

    if today > end_date:
        return 0

    existing = await db.execute(
        select(LifetimeSubscription).where(
            LifetimeSubscription.household_id == household_id,
            LifetimeSubscription.member_id == member.id,
            LifetimeSubscription.product_id == product.id,
            LifetimeSubscription.status == "active",
        )
    )
    if existing.scalar_one_or_none():
        return 0

    sub = LifetimeSubscription(
        household_id=household_id,
        member_id=member.id,
        product_id=product.id,
        quantity_per_delivery=round(qty_per_delivery, 3),
        frequency_days=freq_days,
        start_date=today,
        end_date=end_date,
        next_delivery_date=today,
        status="active",
        source="direct",
        locked_unit_price=product.unit_price_wholesale,
        price_ceiling_pct=ceiling_pct,
    )
    db.add(sub)
    return 1


def _determine_frequency(unit_type: str, daily_qty: float) -> int:
    if unit_type in ("piece", "pack", "pair"):
        if daily_qty * 30 < 1:
            return 365
        if daily_qty * 7 < 1:
            return 90
        if daily_qty * 30 < 4:
            return 30
        return 14
    if unit_type in ("kg", "liter"):
        if daily_qty < 0.1:
            return 30
        if daily_qty < 0.5:
            return 14
        return 7
    return 30


def _frequency_for_age_product(start_age_yrs: float) -> int:
    if start_age_yrs < 1:
        return 30
    if start_age_yrs < 4:
        return 60
    return 365