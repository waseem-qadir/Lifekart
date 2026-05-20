import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.profiling.models import Household, Member
from app.modules.health.models import HealthProfile
from app.modules.profiling.schemas import (
    HouseholdCreate,
    HouseholdUpdate,
    MemberCreate,
    MemberUpdate,
)


class ProfilingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Household ──

    async def create_household(self, user_id: uuid.UUID, data: HouseholdCreate) -> Household:
        existing = await self.db.execute(
            select(Household).where(Household.user_id == user_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("You already have a household profile")

        household = Household(
            user_id=user_id,
            address_line1=data.address_line1,
            address_line2=data.address_line2,
            city=data.city,
            state=data.state,
            pincode=data.pincode,
            lat=data.lat,
            lng=data.lng,
            monthly_grocery_budget=data.monthly_grocery_budget,
            prefer_organic=data.prefer_organic,
        )
        self.db.add(household)
        await self.db.flush()

        for member_data in data.members:
            if member_data.family_relation == "self":
                existing_self = await self.db.execute(
                    select(Member).where(
                        Member.household_id == household.id,
                        Member.family_relation == "self",
                    )
                )
                if existing_self.scalar_one_or_none():
                    continue

            member = Member(
                household_id=household.id,
                full_name=member_data.full_name,
                family_relation=member_data.family_relation,
                date_of_birth=member_data.date_of_birth,
                gender=member_data.gender,
                dietary_preference=member_data.dietary_preference,
                lifestyle_tags=member_data.lifestyle_tags,
            )
            self.db.add(member)
            await self.db.flush()

            health_profile = HealthProfile(
                member_id=member.id,
                existing_conditions=[],
                allergies=[],
            )
            self.db.add(health_profile)

        await self.db.flush()
        return await self._get_household_with_members(household.id)

    async def get_my_household(self, user_id: uuid.UUID) -> Household:
        result = await self.db.execute(
            select(Household).where(Household.user_id == user_id)
        )
        household = result.scalar_one_or_none()
        if not household:
            raise ValueError("Household not found. Create one first.")
        return await self._get_household_with_members(household.id)

    async def update_household(self, user_id: uuid.UUID, data: HouseholdUpdate) -> Household:
        household = await self.get_my_household(user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(household, field, value)
        await self.db.flush()
        await self.db.refresh(household)
        return await self._get_household_with_members(household.id)

    async def _get_household_with_members(self, household_id: uuid.UUID) -> Household:
        result = await self.db.execute(
            select(Household)
            .where(Household.id == household_id)
            .options(selectinload(Household.members))
        )
        return result.scalar_one()

    # ── Members ──

    async def add_member(self, user_id: uuid.UUID, data: MemberCreate) -> Member:
        household = await self.get_my_household(user_id)

        if data.family_relation == "self":
            existing = await self.db.execute(
                select(Member).where(
                    Member.household_id == household.id,
                    Member.family_relation == "self",
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError("Only one 'self' member is allowed per household")

        member = Member(
            household_id=household.id,
            full_name=data.full_name,
            family_relation=data.family_relation,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            dietary_preference=data.dietary_preference,
            lifestyle_tags=data.lifestyle_tags,
        )
        self.db.add(member)
        await self.db.flush()

        health_profile = HealthProfile(
            member_id=member.id,
            existing_conditions=[],
            allergies=[],
        )
        self.db.add(health_profile)
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def get_member(self, member_id: uuid.UUID) -> Member:
        result = await self.db.execute(select(Member).where(Member.id == member_id))
        member = result.scalar_one_or_none()
        if not member:
            raise ValueError("Member not found")
        return member

    async def get_household_members(self, user_id: uuid.UUID) -> list[Member]:
        household = await self.get_my_household(user_id)
        result = await self.db.execute(
            select(Member).where(Member.household_id == household.id)
        )
        return list(result.scalars().all())

    async def update_member(
        self, user_id: uuid.UUID, member_id: uuid.UUID, data: MemberUpdate
    ) -> Member:
        household = await self.get_my_household(user_id)
        member = await self.get_member(member_id)

        if member.household_id != household.id:
            raise ValueError("Member does not belong to your household")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(member, field, value)
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def deactivate_member(self, user_id: uuid.UUID, member_id: uuid.UUID) -> None:
        household = await self.get_my_household(user_id)
        member = await self.get_member(member_id)

        if member.household_id != household.id:
            raise ValueError("Member does not belong to your household")
        if member.family_relation == "self":
            raise ValueError("Cannot deactivate the 'self' member")

        member.is_active = False
        await self.db.flush()