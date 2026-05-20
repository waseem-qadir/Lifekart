import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.legacy.models import LegacyNominee, LegacyActivation
from app.modules.legacy.schemas import (
    LegacyNomineeCreate,
    LegacyNomineeUpdate,
    DeathVerificationRequest,
)
from app.modules.calculator.models import LifetimeSubscription
from app.modules.profiling.models import Household
from app.modules.users.models import User


class LegacyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_household(self, user_id: uuid.UUID) -> Household:
        result = await self.db.execute(select(Household).where(Household.user_id == user_id))
        household = result.scalar_one_or_none()
        if not household:
            raise ValueError("Household not found for this user")
        return household

    async def add_nominee(self, user_id: uuid.UUID, data: LegacyNomineeCreate) -> LegacyNominee:
        household = await self._get_household(user_id)

        if data.is_primary:
            await self._unset_primary(household.id)

        nominee = LegacyNominee(
            household_id=household.id,
            nominee_name=data.nominee_name,
            nominee_relationship=data.nominee_relationship,
            nominee_phone=data.nominee_phone,
            nominee_email=data.nominee_email,
            nominee_aadhaar=data.nominee_aadhaar,
            is_primary=data.is_primary,
        )
        self.db.add(nominee)
        await self.db.commit()
        await self.db.refresh(nominee)
        return nominee

    async def get_nominees(self, user_id: uuid.UUID) -> list[LegacyNominee]:
        household = await self._get_household(user_id)
        result = await self.db.execute(
            select(LegacyNominee)
            .where(LegacyNominee.household_id == household.id)
            .order_by(LegacyNominee.is_primary.desc(), LegacyNominee.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_nominee(self, user_id: uuid.UUID, nominee_id: uuid.UUID, data: LegacyNomineeUpdate) -> LegacyNominee:
        household = await self._get_household(user_id)

        result = await self.db.execute(
            select(LegacyNominee).where(
                LegacyNominee.id == nominee_id,
                LegacyNominee.household_id == household.id,
            )
        )
        nominee = result.scalar_one_or_none()
        if not nominee:
            raise ValueError("Nominee not found")

        if data.is_primary and not nominee.is_primary:
            await self._unset_primary(household.id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(nominee, field, value)

        await self.db.commit()
        await self.db.refresh(nominee)
        return nominee

    async def delete_nominee(self, user_id: uuid.UUID, nominee_id: uuid.UUID) -> None:
        household = await self._get_household(user_id)

        result = await self.db.execute(
            select(LegacyNominee).where(
                LegacyNominee.id == nominee_id,
                LegacyNominee.household_id == household.id,
            )
        )
        nominee = result.scalar_one_or_none()
        if not nominee:
            raise ValueError("Nominee not found")

        activation_check = await self.db.execute(
            select(LegacyActivation).where(
                LegacyActivation.successor_nominee_id == nominee_id,
                LegacyActivation.status.in_(["pending_verification", "verified", "in_progress"]),
            )
        )
        if activation_check.scalar_one_or_none():
            raise ValueError("Cannot delete nominee with active legacy activation")

        await self.db.delete(nominee)
        await self.db.commit()

    async def verify_death_and_activate(
        self, user_id: uuid.UUID, data: DeathVerificationRequest
    ) -> LegacyActivation:
        household = await self._get_household(user_id)

        result = await self.db.execute(
            select(LegacyNominee).where(
                LegacyNominee.id == data.nominee_id,
                LegacyNominee.household_id == household.id,
            )
        )
        nominee = result.scalar_one_or_none()
        if not nominee:
            raise ValueError("Nominee not found")

        existing = await self.db.execute(
            select(LegacyActivation).where(
                LegacyActivation.household_id == household.id,
                LegacyActivation.status.in_(["pending_verification", "verified", "in_progress"]),
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("An active legacy activation already exists for this household")

        active_subs_result = await self.db.execute(
            select(func.count(LifetimeSubscription.id)).where(
                LifetimeSubscription.household_id == household.id,
                LifetimeSubscription.status == "active",
            )
        )
        sub_count = active_subs_result.scalar_one()

        activation = LegacyActivation(
            household_id=household.id,
            original_user_id=user_id,
            successor_nominee_id=nominee.id,
            active_subscriptions_count=sub_count,
            status="pending_verification",
            death_certificate_url=data.proof_document_url,
            activation_notes=data.notes,
        )
        self.db.add(activation)

        await self.db.commit()
        await self.db.refresh(activation)
        return activation

    async def approve_activation(self, activation_id: uuid.UUID) -> LegacyActivation:
        result = await self.db.execute(
            select(LegacyActivation).where(LegacyActivation.id == activation_id)
        )
        activation = result.scalar_one_or_none()
        if not activation:
            raise ValueError("Activation not found")

        if activation.status != "pending_verification":
            raise ValueError(f"Activation is in status '{activation.status}', expected 'pending_verification'")

        now = datetime.utcnow()
        activation.status = "verified"
        activation.deceased_verified_at = now

        result = await self.db.execute(
            select(LegacyNominee).where(LegacyNominee.id == activation.successor_nominee_id)
        )
        nominee = result.scalar_one()
        nominee.is_verified = True
        nominee.verification_status = "verified"

        result = await self.db.execute(
            select(Household).where(Household.id == nominee.household_id)
        )
        original_household = result.scalar_one()

        result = await self.db.execute(
            select(User).where(User.id == original_household.user_id)
        )
        user = result.scalar_one()
        user.is_active = False

        new_household = Household(
            address_line1=original_household.address_line1,
            address_line2=original_household.address_line2,
            city=original_household.city,
            state=original_household.state,
            pincode=original_household.pincode,
            monthly_grocery_budget=original_household.monthly_grocery_budget,
            prefer_organic=original_household.prefer_organic,
        )
        self.db.add(new_household)
        await self.db.flush()

        activation.transfer_household_id = new_household.id
        activation.activated_at = now
        activation.status = "in_progress"

        result = await self.db.execute(
            select(LifetimeSubscription).where(
                LifetimeSubscription.household_id == nominee.household_id,
                LifetimeSubscription.status == "active",
            )
        )
        old_subs = list(result.scalars().all())

        today = date.today()
        inherited_end_date = date(today.year + 50, today.month, today.day)

        transferred = 0
        for old_sub in old_subs:
            old_end_date = old_sub.end_date
            old_sub.end_date = today
            old_sub.status = "legacy_transferred"

            new_sub = LifetimeSubscription(
                household_id=new_household.id,
                member_id=old_sub.member_id,
                product_id=old_sub.product_id,
                quantity_per_delivery=old_sub.quantity_per_delivery,
                frequency_days=old_sub.frequency_days,
                start_date=today + timedelta(days=1),
                end_date=inherited_end_date,
                next_delivery_date=old_sub.next_delivery_date,
                status="active",
                source="legacy",
                source_id=activation.id,
                locked_unit_price=old_sub.locked_unit_price,
                price_ceiling_pct=old_sub.price_ceiling_pct,
            )
            self.db.add(new_sub)
            transferred += 1

        activation.transferred_count = transferred
        activation.status = "completed"
        activation.activation_notes = (
            f"{(activation.activation_notes or '').rstrip('.')}. "
            f"{transferred} subscriptions transferred to new household."
        ).strip()

        await self.db.commit()
        await self.db.refresh(activation)
        return activation

    async def _unset_primary(self, household_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(LegacyNominee).where(
                LegacyNominee.household_id == household_id,
                LegacyNominee.is_primary == True,
            )
        )
        for nominee in result.scalars().all():
            nominee.is_primary = False