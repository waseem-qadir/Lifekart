import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.scheduling.models import DeliveryEvent
from app.modules.profiling.models import Household

class SchedulingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_my_deliveries(self, user_id: uuid.UUID) -> list[DeliveryEvent]:
        # get household
        h_res = await self.db.execute(select(Household).where(Household.user_id == user_id))
        household = h_res.scalar_one_or_none()
        if not household:
            return []
            
        res = await self.db.execute(
            select(DeliveryEvent)
            .options(joinedload(DeliveryEvent.product))
            .where(DeliveryEvent.household_id == household.id)
            .order_by(DeliveryEvent.scheduled_date.desc())
        )
        return list(res.scalars().all())
