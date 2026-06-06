import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.scheduling.models import (
    PriceHistory,
    PriceProtectionRule,
    SubstitutionEvent,
)
from app.modules.calculator.models import LifetimeSubscription
from app.modules.catalog.models import Product
from app.modules.profiling.models import Household
from app.modules.price_protect.schemas import (
    PriceProtectionRuleCreate,
    SubstitutionEventCreate,
)


class PriceProtectionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_rule(self, data: PriceProtectionRuleCreate) -> PriceProtectionRule:
        rule = PriceProtectionRule(
            product_id=data.product_id,
            ceiling_price=data.ceiling_price,
            max_annual_increase_pct=data.max_annual_increase_pct,
            effective_from=data.effective_from,
            effective_to=data.effective_to,
        )
        self.db.add(rule)
        await self.db.flush()
        await self.db.refresh(rule)
        return rule

    async def get_rules(self, product_id: uuid.UUID | None = None) -> list[PriceProtectionRule]:
        query = select(PriceProtectionRule)
        if product_id:
            query = query.where(PriceProtectionRule.product_id == product_id)
        result = await self.db.execute(query.order_by(PriceProtectionRule.effective_from.desc()))
        return list(result.scalars().all())

    async def get_rule(self, rule_id: uuid.UUID) -> PriceProtectionRule:
        result = await self.db.execute(
            select(PriceProtectionRule).where(PriceProtectionRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        if not rule:
            raise ValueError("Price protection rule not found")
        return rule

    async def delete_rule(self, rule_id: uuid.UUID) -> None:
        rule = await self.get_rule(rule_id)
        await self.db.delete(rule)
        await self.db.flush()

    async def get_price_history(
        self, product_id: uuid.UUID, limit: int = 30
    ) -> list[PriceHistory]:
        result = await self.db.execute(
            select(PriceHistory)
            .where(PriceHistory.product_id == product_id)
            .order_by(PriceHistory.recorded_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def record_price(self, product_id: uuid.UUID, wholesale: float, retail: float) -> PriceHistory:
        history = PriceHistory(
            product_id=product_id,
            wholesale_price=wholesale,
            retail_price=retail,
        )
        self.db.add(history)
        await self.db.flush()
        await self.db.refresh(history)
        return history

    async def add_substitution(
        self, user_id: uuid.UUID, data: SubstitutionEventCreate
    ) -> SubstitutionEvent:
        result = await self.db.execute(
            select(LifetimeSubscription).where(
                LifetimeSubscription.id == data.lifetime_subscription_id
            )
        )
        sub = result.scalar_one_or_none()
        if not sub:
            raise ValueError("Subscription not found")

        result = await self.db.execute(
            select(Household).where(
                Household.id == sub.household_id,
                Household.user_id == user_id,
            )
        )
        if not result.scalar_one_or_none():
            raise ValueError("Not your subscription")

        event = SubstitutionEvent(
            lifetime_subscription_id=data.lifetime_subscription_id,
            original_product_id=sub.product_id,
            substituted_product_id=data.substitute_product_id,
            reason=data.reason,
            is_user_approved=True,
        )
        self.db.add(event)

        sub.product_id = data.substitute_product_id
        sub.locked_unit_price = await self._get_product_price(data.substitute_product_id)

        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def get_substitutions(
        self, user_id: uuid.UUID, subscription_id: uuid.UUID
    ) -> list[SubstitutionEvent]:
        result = await self.db.execute(
            select(LifetimeSubscription).where(LifetimeSubscription.id == subscription_id)
        )
        sub = result.scalar_one_or_none()
        if not sub:
            raise ValueError("Subscription not found")

        result = await self.db.execute(
            select(Household).where(
                Household.id == sub.household_id,
                Household.user_id == user_id,
            )
        )
        if not result.scalar_one_or_none():
            raise ValueError("Not your subscription")

        result = await self.db.execute(
            select(SubstitutionEvent)
            .where(SubstitutionEvent.lifetime_subscription_id == subscription_id)
            .order_by(SubstitutionEvent.substituted_at.desc())
        )
        return list(result.scalars().all())

    async def get_all_user_substitutions(self, user_id: uuid.UUID) -> list[dict]:
        from sqlalchemy.orm import joinedload
        result = await self.db.execute(
            select(SubstitutionEvent)
            .join(LifetimeSubscription)
            .join(Household)
            .options(
                joinedload(SubstitutionEvent.subscription).joinedload(LifetimeSubscription.product)
            )
            .where(Household.user_id == user_id)
            .order_by(SubstitutionEvent.substituted_at.desc())
        )
        events = result.scalars().all()
        # We need to return product names as well
        out = []
        for e in events:
            # We need the original product name and substitute product name
            orig_prod = await self.db.execute(select(Product).where(Product.id == e.original_product_id))
            orig_p = orig_prod.scalar_one_or_none()
            sub_prod = await self.db.execute(select(Product).where(Product.id == e.substituted_product_id))
            sub_p = sub_prod.scalar_one_or_none()
            out.append({
                "id": str(e.id),
                "lifetime_subscription_id": str(e.lifetime_subscription_id),
                "original_product_name": orig_p.name if orig_p else "Unknown",
                "substituted_product_name": sub_p.name if sub_p else "Unknown",
                "reason": e.reason,
                "substitution_type": e.substitution_type,
                "substituted_at": e.substituted_at.isoformat(),
            })
        return out

    async def get_user_savings(self, user_id: uuid.UUID) -> dict:
        result = await self.db.execute(
            select(LifetimeSubscription)
            .join(Household)
            .where(
                Household.user_id == user_id,
                LifetimeSubscription.status == "active"
            )
        )
        subs = result.scalars().all()

        current_month_savings = 0.0
        total_saved_historical = 0.0

        # Calculate historical savings from past deliveries
        from app.modules.scheduling.models import DeliveryEvent
        from sqlalchemy.orm import joinedload
        if subs:
            sub_ids = [sub.id for sub in subs]
            result_del = await self.db.execute(
                select(DeliveryEvent)
                .options(joinedload(DeliveryEvent.product))
                .where(DeliveryEvent.subscription_id.in_(sub_ids), DeliveryEvent.status == "delivered")
            )
            deliveries = result_del.scalars().all()
            for d in deliveries:
                prod = d.product
                if prod and prod.unit_price_retail > d.unit_price_applied:
                    diff = float(prod.unit_price_retail - d.unit_price_applied)
                    total_saved_historical += diff * d.quantity

        for sub in subs:
            prod_result = await self.db.execute(select(Product).where(Product.id == sub.product_id))
            product = prod_result.scalar_one_or_none()
            if not product:
                continue
            
            # If current catalog retail price is higher than the locked price, they are saving money!
            if product.unit_price_retail > sub.locked_unit_price:
                diff = float(product.unit_price_retail - sub.locked_unit_price)
                
                # Monthly savings: diff * quantity * deliveries_per_month
                deliveries_per_month = 30 / sub.frequency_days if sub.frequency_days else 1
                monthly = diff * sub.quantity_per_delivery * deliveries_per_month
                
                current_month_savings += monthly

        return {
            "current_month_savings": current_month_savings,
            "total_saved": total_saved_historical
        }

    async def _get_product_price(self, product_id: uuid.UUID):
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        return product.unit_price_wholesale if product else 0

    async def check_ceiling_breaches(self) -> list[dict]:
        from collections import defaultdict
        from sqlalchemy.orm import joinedload
        from app.modules.scheduling.models import PriceCeilingAlert

        result = await self.db.execute(
            select(LifetimeSubscription)
            .options(joinedload(LifetimeSubscription.product))
            .where(
                LifetimeSubscription.status == "active",
                LifetimeSubscription.price_ceiling_pct > 0,
            )
        )
        subscriptions = result.unique().scalars().all()

        product_breaches: dict[uuid.UUID, dict] = defaultdict(
            lambda: {"households": 0, "locked_ceiling": None, "product": None}
        )

        for sub in subscriptions:
            product = sub.product
            if not product:
                continue

            allowed_max = sub.locked_unit_price * (1 + sub.price_ceiling_pct / 100)
            if product.unit_price_wholesale > allowed_max:
                product_breaches[product.id]["households"] += 1
                product_breaches[product.id]["locked_ceiling"] = \
                    max(product_breaches[product.id]["locked_ceiling"] or 0, allowed_max)
                product_breaches[product.id]["product"] = product

        alerts = []
        for product_id, breach in product_breaches.items():
            product = breach["product"]

            alert = PriceCeilingAlert(
                product_id=product_id,
                current_catalog_price=product.unit_price_wholesale,
                locked_ceiling=breach["locked_ceiling"],
                affected_households=breach["households"],
            )
            self.db.add(alert)
            alerts.append({
                "product_id": str(product_id),
                "product_name": product.name,
                "current_catalog_price": str(product.unit_price_wholesale),
                "locked_ceiling": str(breach["locked_ceiling"]),
                "affected_households": breach["households"],
                "action": "alert_manufacturer",
            })

        await self.db.commit()
        return alerts

    async def check_stock_and_substitute(self) -> list[dict]:
        from sqlalchemy.orm import joinedload
        from app.modules.catalog.models import ProductSubstitute

        result = await self.db.execute(
            select(LifetimeSubscription)
            .options(joinedload(LifetimeSubscription.product))
            .where(LifetimeSubscription.status == "active")
        )
        subscriptions = result.unique().scalars().all()

        unavailable_product_ids = [
            sub.product_id for sub in subscriptions
            if sub.product and (not sub.product.is_active or sub.product.stock_quantity <= 0)
        ]

        if not unavailable_product_ids:
            return []

        product_ids_set = set(unavailable_product_ids)

        sub_links_result = await self.db.execute(
            select(ProductSubstitute)
            .options(joinedload(ProductSubstitute.substitute_product))
            .where(ProductSubstitute.product_id.in_(product_ids_set))
            .order_by(ProductSubstitute.priority_rank)
        )
        substitute_links = sub_links_result.unique().scalars().all()

        best_substitute: dict[uuid.UUID, Product] = {}
        for link in substitute_links:
            if link.product_id not in best_substitute and link.substitute_product:
                if link.substitute_product.is_active and link.substitute_product.stock_quantity > 0:
                    best_substitute[link.product_id] = link.substitute_product

        swapped = []
        for sub in subscriptions:
            product = sub.product
            if not product:
                continue

            if sub.product_id not in product_ids_set:
                continue

            alt_product = best_substitute.get(sub.product_id)
            if not alt_product:
                continue

            reason = "out_of_stock" if product.stock_quantity <= 0 else "discontinued"
            sub_type = "TEMPORARY" if reason == "out_of_stock" else "PERMANENT"

            event = SubstitutionEvent(
                lifetime_subscription_id=sub.id,
                original_product_id=product.id,
                substituted_product_id=alt_product.id,
                reason=reason,
                substitution_type=sub_type,
                is_user_approved=False,
            )
            self.db.add(event)
            sub.product_id = alt_product.id
            sub.locked_unit_price = alt_product.unit_price_wholesale

            swapped.append({
                "subscription_id": str(sub.id),
                "old_product": product.name,
                "new_product": alt_product.name,
                "reason": reason,
            })

        await self.db.commit()
        return swapped