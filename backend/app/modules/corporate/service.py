import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.corporate.models import CorporatePartner, EmployeeEnrollment
from app.modules.corporate.schemas import (
    CorporatePartnerCreate,
    CorporatePartnerUpdate,
    EmployeeEnrollCreate,
)


class CorporateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_partner(self, user_id: uuid.UUID, data: CorporatePartnerCreate) -> CorporatePartner:
        existing = await self.db.execute(
            select(CorporatePartner).where(CorporatePartner.user_id == user_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Corporate profile already exists for this user")

        if data.gstin:
            result = await self.db.execute(
                select(CorporatePartner).where(CorporatePartner.gstin == data.gstin)
            )
            if result.scalar_one_or_none():
                raise ValueError("A partner with this GSTIN already exists")

        partner = CorporatePartner(
            user_id=user_id,
            company_name=data.company_name,
            gstin=data.gstin,
            industry=data.industry,
            employee_count=data.employee_count,
            contact_email=data.contact_email,
            address_line1=data.address_line1,
            city=data.city,
            state=data.state,
            pincode=data.pincode,
            subsidy_percentage=data.subsidy_percentage,
            max_employee_benefit=data.max_employee_benefit,
        )
        self.db.add(partner)
        await self.db.flush()
        await self.db.refresh(partner)
        return partner

    async def get_my_partner(self, user_id: uuid.UUID) -> CorporatePartner:
        result = await self.db.execute(
            select(CorporatePartner).where(CorporatePartner.user_id == user_id)
        )
        partner = result.scalar_one_or_none()
        if not partner:
            raise ValueError("Corporate profile not found")
        return partner

    async def update_partner(self, user_id: uuid.UUID, data: CorporatePartnerUpdate) -> CorporatePartner:
        partner = await self.get_my_partner(user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(partner, field, value)
        await self.db.flush()
        await self.db.refresh(partner)
        return partner

    async def enroll_employee(self, user_id: uuid.UUID, data: EmployeeEnrollCreate) -> EmployeeEnrollment:
        partner = await self.get_my_partner(user_id)
        if partner.partnership_status != "active":
            raise ValueError("Corporate partnership is not yet active")

        existing = await self.db.execute(
            select(EmployeeEnrollment).where(
                EmployeeEnrollment.corporate_id == partner.id,
                EmployeeEnrollment.household_id == data.household_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("This household is already enrolled")

        enrollment = EmployeeEnrollment(
            corporate_id=partner.id,
            household_id=data.household_id,
            employee_id=data.employee_id,
            department=data.department,
            designation=data.designation,
        )
        self.db.add(enrollment)
        await self.db.flush()
        await self.db.refresh(enrollment)
        return enrollment

    async def get_employees(self, user_id: uuid.UUID) -> list[EmployeeEnrollment]:
        partner = await self.get_my_partner(user_id)
        result = await self.db.execute(
            select(EmployeeEnrollment).where(
                EmployeeEnrollment.corporate_id == partner.id,
                EmployeeEnrollment.is_active == True,
            )
        )
        return list(result.scalars().all())

    async def remove_employee(self, user_id: uuid.UUID, enrollment_id: uuid.UUID) -> None:
        partner = await self.get_my_partner(user_id)
        result = await self.db.execute(
            select(EmployeeEnrollment).where(
                EmployeeEnrollment.id == enrollment_id,
                EmployeeEnrollment.corporate_id == partner.id,
            )
        )
        enrollment = result.scalar_one_or_none()
        if not enrollment:
            raise ValueError("Enrollment not found")
        enrollment.is_active = False
        await self.db.flush()

    async def approve_partner(self, partner_id: uuid.UUID) -> CorporatePartner:
        result = await self.db.execute(
            select(CorporatePartner).where(CorporatePartner.id == partner_id)
        )
        partner = result.scalar_one_or_none()
        if not partner:
            raise ValueError("Corporate partner not found")
        if partner.partnership_status != "pending":
            raise ValueError(f"Cannot approve partner with status '{partner.partnership_status}'")
        partner.partnership_status = "active"
        partner.agreement_signed_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(partner)
        return partner

    async def list_all_partners(self) -> list[CorporatePartner]:
        result = await self.db.execute(select(CorporatePartner))
        return list(result.scalars().all())