import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.community.models import CommunityGroup, CommunityMembership, CommunityOrder
from app.modules.community.schemas import CommunityGroupCreate
from app.modules.profiling.models import Household


class CommunityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_group(self, user_id: uuid.UUID, data: CommunityGroupCreate) -> CommunityGroup:
        result = await self.db.execute(select(Household).where(Household.user_id == user_id))
        household = result.scalar_one_or_none()
        if not household:
            raise ValueError("Create your household first")

        group = CommunityGroup(
            name=data.name,
            locality=data.locality,
            city=data.city,
            state=data.state,
            pincode=data.pincode,
            admin_household_id=household.id,
            min_households_for_pooling=data.min_households_for_pooling,
        )
        self.db.add(group)
        await self.db.flush()

        membership = CommunityMembership(group_id=group.id, household_id=household.id)
        self.db.add(membership)
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def get_groups(self, pincode: str | None = None) -> list[CommunityGroup]:
        query = select(CommunityGroup).where(
            CommunityGroup.status.in_(["active", "forming"])
        )
        if pincode:
            query = query.where(CommunityGroup.pincode == pincode)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def join_group(self, user_id: uuid.UUID, group_id: uuid.UUID) -> CommunityMembership:
        result = await self.db.execute(select(Household).where(Household.user_id == user_id))
        household = result.scalar_one_or_none()
        if not household:
            raise ValueError("Create your household first")

        result = await self.db.execute(
            select(CommunityGroup).where(CommunityGroup.id == group_id)
        )
        group = result.scalar_one_or_none()
        if not group:
            raise ValueError("Group not found")

        existing = await self.db.execute(
            select(CommunityMembership).where(
                CommunityMembership.group_id == group_id,
                CommunityMembership.household_id == household.id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Already a member of this group")

        membership = CommunityMembership(group_id=group_id, household_id=household.id)
        self.db.add(membership)
        await self.db.flush()

        count_result = await self.db.execute(
            select(func.count(CommunityMembership.id)).where(
                CommunityMembership.group_id == group_id
            )
        )
        member_count = count_result.scalar_one()
        if member_count >= group.min_households_for_pooling and group.status == "forming":
            group.status = "active"

        await self.db.commit()
        await self.db.refresh(membership)
        return membership