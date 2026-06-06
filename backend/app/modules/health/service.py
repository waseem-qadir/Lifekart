import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.health.models import HealthProfile, HealthTransition, HealthRule
from app.modules.health.schemas import HealthProfileUpdate, HealthTransitionCreate
from app.modules.calculator.models import LifetimeSubscription
from app.modules.catalog.models import Product, ProductCategory
from app.modules.catalog.service import CatalogService
from app.modules.profiling.models import Member, Household
from app.core.config import settings


class HealthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile(self, member_id: uuid.UUID) -> HealthProfile:
        result = await self.db.execute(
            select(HealthProfile).where(HealthProfile.member_id == member_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise ValueError("Health profile not found")
        return profile

    async def update_profile(self, member_id: uuid.UUID, data: HealthProfileUpdate) -> HealthProfile:
        profile = await self.get_profile(member_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def create_transition(
        self, user_id: uuid.UUID, data: HealthTransitionCreate
    ) -> HealthTransition:
        result = await self.db.execute(
            select(HealthProfile).where(HealthProfile.id == data.health_profile_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise ValueError("Health profile not found")

        result = await self.db.execute(
            select(Member).where(Member.id == profile.member_id)
        )
        member = result.scalar_one_or_none()
        if not member:
            raise ValueError("Member not found")

        result = await self.db.execute(
            select(Household).where(
                Household.id == member.household_id,
                Household.user_id == user_id,
            )
        )
        if not result.scalar_one_or_none():
            raise ValueError("Not your household member")

        transition = HealthTransition(
            health_profile_id=data.health_profile_id,
            transition_type=data.transition_type,
            condition_name=data.condition_name,
            trigger_date=data.trigger_date,
            affected_subscriptions=data.affected_subscriptions,
            notes=data.notes,
        )
        self.db.add(transition)
        await self.db.commit()
        await self.db.refresh(transition)
        return transition

    async def get_transitions(self, member_id: uuid.UUID) -> list[HealthTransition]:
        result = await self.db.execute(
            select(HealthProfile).where(HealthProfile.member_id == member_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            return []

        result = await self.db.execute(
            select(HealthTransition)
            .where(HealthTransition.health_profile_id == profile.id)
            .order_by(HealthTransition.trigger_date.desc())
        )
        return list(result.scalars().all())

    async def process_transition(self, transition_id: uuid.UUID) -> dict:
        result = await self.db.execute(
            select(HealthTransition).where(
                HealthTransition.id == transition_id,
                HealthTransition.is_applied == False,
            )
        )
        transition = result.scalar_one_or_none()
        if not transition:
            raise ValueError("Transition not found or already applied")

        profile = await self.get_profile(transition.health_profile_id)

        result = await self.db.execute(
            select(Member).where(Member.id == profile.member_id)
        )
        member = result.scalar_one()

        today = date.today()

        if transition.transition_type == "condition_added" and transition.condition_name:
            current = set(profile.existing_conditions or [])
            current.add(transition.condition_name)
            profile.existing_conditions = list(current)

        elif transition.transition_type == "condition_removed" and transition.condition_name:
            current = set(profile.existing_conditions or [])
            current.discard(transition.condition_name)
            profile.existing_conditions = list(current)

        affected = transition.affected_subscriptions or {}
        manual_remove = set(affected.get("remove", []))
        manual_add = set(affected.get("add", []))

        result = await self.db.execute(
            select(LifetimeSubscription)
            .options(joinedload(LifetimeSubscription.product))
            .where(
                LifetimeSubscription.household_id == member.household_id,
                LifetimeSubscription.status == "active",
            )
        )
        active_subs = list(result.unique().scalars().all())

        health_rule = None
        if transition.condition_name:
            result = await self.db.execute(
                select(HealthRule).where(HealthRule.condition_name == transition.condition_name)
            )
            health_rule = result.scalar_one_or_none()

        swaps = []
        catalog = CatalogService(self.db)

        for sub in active_subs:
            product = sub.product
            if not product:
                continue

            product_tags = set(product.health_tags or [])

            if product.sku in manual_remove:
                closed_subs = [{
                    "original_end_date": sub.end_date,
                    "quantity_per_delivery": sub.quantity_per_delivery,
                    "frequency_days": sub.frequency_days,
                    "locked_unit_price": sub.locked_unit_price,
                    "price_ceiling_pct": sub.price_ceiling_pct,
                }]
                swap_reason = "manual"
            elif health_rule:
                forbidden = set(health_rule.forbidden_tags or [])
                if not product_tags & forbidden:
                    continue

                closed_subs = [{
                    "original_end_date": sub.end_date,
                    "quantity_per_delivery": sub.quantity_per_delivery,
                    "frequency_days": sub.frequency_days,
                    "locked_unit_price": sub.locked_unit_price,
                    "price_ceiling_pct": sub.price_ceiling_pct,
                }]
                swap_reason = f"forbidden_tags:{','.join(sorted(forbidden))}"
            else:
                continue

            sub.end_date = today
            sub.status = "completed"
            swaps.append({
                "action": "removed",
                "product_name": product.name,
                "sku": product.sku,
                "subscription_id": str(sub.id),
                "reason": swap_reason,
            })

            replacement = None
            if product.sku in manual_remove:
                for add_sku in manual_add:
                    add_result = await self.db.execute(
                        select(Product).where(Product.sku == add_sku, Product.is_active == True)
                    )
                    candidate = add_result.scalar_one_or_none()
                    if candidate and candidate.category_id == product.category_id:
                        replacement = candidate
                        break
            elif health_rule:
                required = list(set(health_rule.required_tags or []))
                forbidden = list(set(health_rule.forbidden_tags or []))
                replacement = await catalog.find_healthy_alternative(
                    product.id, required_tags=required, forbidden_tags=forbidden
                )

            if replacement is None:
                swaps.append({
                    "action": "no_replacement",
                    "product_name": product.name,
                    "sku": product.sku,
                    "reason": swap_reason,
                })
                continue

            for closed in closed_subs:
                inherited_end_date = closed["original_end_date"]

                new_sub = LifetimeSubscription(
                    household_id=member.household_id,
                    member_id=member.id,
                    product_id=replacement.id,
                    quantity_per_delivery=closed["quantity_per_delivery"],
                    frequency_days=closed["frequency_days"],
                    start_date=today,
                    end_date=inherited_end_date,
                    next_delivery_date=today,
                    status="active",
                    source="health_transition",
                    source_id=transition.id,
                    locked_unit_price=closed["locked_unit_price"],
                    price_ceiling_pct=closed["price_ceiling_pct"],
                )
                self.db.add(new_sub)
                swaps.append({
                    "action": "added",
                    "product_name": replacement.name,
                    "sku": replacement.sku,
                    "end_date": str(inherited_end_date),
                    "reason": swap_reason,
                })

        transition.is_applied = True
        await self.db.commit()
        return {"transition_id": str(transition_id), "swaps": swaps}