import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calculator.models import LifetimeSubscription
from app.modules.calculator.schemas import SubscriptionUpdate
from app.modules.profiling.models import Household


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
        )
        if status:
            query = query.where(LifetimeSubscription.status == status)
        query = query.order_by(LifetimeSubscription.start_date)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_subscription(self, subscription_id: uuid.UUID) -> LifetimeSubscription:
        result = await self.db.execute(
            select(LifetimeSubscription).where(LifetimeSubscription.id == subscription_id)
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
        await self.db.flush()
        await self.db.refresh(sub)
        return sub

    async def pause_subscription(self, user_id: uuid.UUID, subscription_id: uuid.UUID) -> LifetimeSubscription:
        sub = await self.get_subscription(subscription_id)
        await self._verify_ownership(user_id, sub.household_id)
        if sub.status != "active":
            raise ValueError(f"Cannot pause a subscription with status '{sub.status}'")
        sub.status = "paused"
        await self.db.flush()
        await self.db.refresh(sub)
        return sub

    async def resume_subscription(self, user_id: uuid.UUID, subscription_id: uuid.UUID) -> LifetimeSubscription:
        sub = await self.get_subscription(subscription_id)
        await self._verify_ownership(user_id, sub.household_id)
        if sub.status != "paused":
            raise ValueError(f"Cannot resume a subscription with status '{sub.status}'")
        sub.status = "active"
        await self.db.flush()
        await self.db.refresh(sub)
        return sub

    async def cancel_subscription(self, user_id: uuid.UUID, subscription_id: uuid.UUID) -> None:
        sub = await self.get_subscription(subscription_id)
        await self._verify_ownership(user_id, sub.household_id)
        sub.status = "cancelled"
        await self.db.flush()

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
            ).order_by(LifetimeSubscription.start_date).limit(1)
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