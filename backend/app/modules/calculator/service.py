import uuid
from datetime import date, timedelta, datetime
from app.core.config import settings
from app.modules.agreements.models import WholesaleAgreement, AgreementItem
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.calculator.models import LifetimeSubscription
from app.modules.calculator.schemas import SubscriptionUpdate
from app.modules.profiling.models import Household
from app.modules.catalog.models import Product


class SubscriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_my_subscriptions(
        self, user_id: uuid.UUID, status: str | None = None
    ) -> list[LifetimeSubscription]:
        result = await self.db.execute(
            select(Household).where(Household.user_id == user_id)
        )
        household = result.scalar_one_or_none()
        if not household:
            return []

        query = select(LifetimeSubscription).where(
            LifetimeSubscription.household_id == household.id
        ).options(selectinload(LifetimeSubscription.product))
        if status:
            query = query.where(LifetimeSubscription.status == status)
        query = query.order_by(LifetimeSubscription.start_date)

        result = await self.db.execute(query)
        return list(result.unique().scalars().all())

    async def get_subscription(self, subscription_id: uuid.UUID) -> LifetimeSubscription:
        result = await self.db.execute(
            select(LifetimeSubscription)
            .where(LifetimeSubscription.id == subscription_id)
            .options(selectinload(LifetimeSubscription.product))
        )
        sub = result.scalar_one_or_none()
        if not sub:
            raise ValueError("Subscription not found")
        return sub

    async def update_subscription(
        self, user_id: uuid.UUID, subscription_id: uuid.UUID, data: SubscriptionUpdate
    ) -> LifetimeSubscription:
        sub = await self.get_subscription(subscription_id)
        await self._verify_ownership(user_id, sub.household_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(sub, field, value)
        await self.db.commit()
        await self.db.refresh(sub)
        return sub

    async def pause_subscription(self, user_id: uuid.UUID, subscription_id: uuid.UUID) -> LifetimeSubscription:
        sub = await self.get_subscription(subscription_id)
        await self._verify_ownership(user_id, sub.household_id)
        if sub.status != "active":
            raise ValueError(f"Cannot pause a subscription with status '{sub.status}'")
            
        # Logistics Cutoff Rule
        # Eagerly load manufacturer lead time from product (assuming product.manufacturer is not explicitly loaded, 
        # but wait, `get_subscription` only loads `product`. We should fetch it explicitly to be safe).
        result = await self.db.execute(
            select(LifetimeSubscription)
            .where(LifetimeSubscription.id == subscription_id)
            .options(selectinload(LifetimeSubscription.product).selectinload(Product.manufacturer))
        )
        sub_with_mfg = result.scalar_one()
        lead_time = sub_with_mfg.product.manufacturer.lead_time_days if sub_with_mfg.product.manufacturer else 14
        
        days_until_delivery = (sub.next_delivery_date - date.today()).days
        if days_until_delivery <= lead_time:
            sub.pause_after_next_delivery = True
            # Keep status as 'active' until the delivery actually happens
            # But the user sees it's flagged to pause
        else:
            sub.status = "paused"
            sub.paused_at = datetime.utcnow()
            
        await self.db.commit()
        await self.db.refresh(sub)
        return sub

    async def resume_subscription(self, user_id: uuid.UUID, subscription_id: uuid.UUID) -> LifetimeSubscription:
        sub = await self.get_subscription(subscription_id)
        await self._verify_ownership(user_id, sub.household_id)
        
        if sub.status == "contract_breached":
            raise ValueError("Grace period expired. You must sign a new agreement at today's price.")
            
        if sub.status not in ("paused", "suggested", "active"):
            raise ValueError(f"Cannot resume a subscription with status '{sub.status}'")

        # If it was active but pause_after_next_delivery was set, clear it to cancel the pending pause
        sub.pause_after_next_delivery = False
        sub.paused_at = None

        if sub.source == "ai_generated":
            duration_days = int(settings.MAX_LIFETIME_YEARS * 365.25)
            yearly_value = float(sub.locked_unit_price) * sub.quantity_per_delivery * (365 / sub.frequency_days)
            total_item_value = yearly_value * settings.MAX_LIFETIME_YEARS

            new_agreement = WholesaleAgreement(
                household_id=sub.household_id,
                manufacturer_id=sub.product.manufacturer_id,
                status="active",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=duration_days),
                price_ceiling_agreed=sub.price_ceiling_pct,
                total_contract_value=total_item_value,
                signed_at=datetime.utcnow()
            )
            self.db.add(new_agreement)
            await self.db.flush()

            new_item = AgreementItem(
                agreement_id=new_agreement.id,
                product_id=sub.product_id,
                locked_unit_price=sub.locked_unit_price,
                committed_monthly_qty=round(sub.quantity_per_delivery * (30 / sub.frequency_days), 2),
                frequency_days=sub.frequency_days,
                total_item_value=total_item_value
            )
            self.db.add(new_item)

            sub.source = "agreement"
            sub.source_id = new_agreement.id

        sub.status = "active"
        await self.db.commit()
        await self.db.refresh(sub)
        return sub

    async def cancel_subscription(self, user_id: uuid.UUID, subscription_id: uuid.UUID) -> None:
        sub = await self.get_subscription(subscription_id)
        await self._verify_ownership(user_id, sub.household_id)
        sub.status = "cancelled"
        await self.db.commit()

    async def adjust_size(
        self, user_id: uuid.UUID, subscription_id: uuid.UUID
    ) -> LifetimeSubscription:
        sub = await self.get_subscription(subscription_id)
        await self._verify_ownership(user_id, sub.household_id)

        result = await self.db.execute(
            select(LifetimeSubscription).where(
                LifetimeSubscription.household_id == sub.household_id,
                LifetimeSubscription.member_id == sub.member_id,
                LifetimeSubscription.start_date >= sub.start_date,
                LifetimeSubscription.id != sub.id,
                LifetimeSubscription.status.in_(["active", "paused"]),
            )
            .options(selectinload(LifetimeSubscription.product))
            .order_by(LifetimeSubscription.start_date).limit(1)
        )
        next_sub = result.scalar_one_or_none()

        sub.end_date = date.today()
        sub.status = "completed"

        if next_sub:
            next_sub.start_date = date.today() + timedelta(days=1)
            next_sub.next_delivery_date = date.today() + timedelta(days=1)
            await self.db.flush()
            await self.db.refresh(next_sub)
            return next_sub

        await self.db.flush()
        raise ValueError("No next size subscription found — re-run calculator to regenerate")

    async def _verify_ownership(self, user_id: uuid.UUID, household_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(Household).where(
                Household.id == household_id,
                Household.user_id == user_id,
            )
        )
        if not result.scalar_one_or_none():
            raise ValueError("Subscription does not belong to you")