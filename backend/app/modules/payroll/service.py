import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payroll.models import PayrollDeduction
from app.modules.corporate.models import EmployeeEnrollment, CorporatePartner
from app.modules.payroll.schemas import PayrollDeductionCreate


class PayrollService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_deduction(self, user_id: uuid.UUID, data: PayrollDeductionCreate) -> PayrollDeduction:
        result = await self.db.execute(
            select(CorporatePartner).where(CorporatePartner.user_id == user_id)
        )
        partner = result.scalar_one_or_none()
        if not partner:
            raise ValueError("Corporate profile not found")

        result = await self.db.execute(
            select(EmployeeEnrollment).where(
                EmployeeEnrollment.id == data.employee_enrollment_id,
                EmployeeEnrollment.corporate_id == partner.id,
            )
        )
        if not result.scalar_one_or_none():
            raise ValueError("Employee not enrolled under your company")

        amount = data.subscription_value - data.employer_subsidy
        deduction = PayrollDeduction(
            employee_enrollment_id=data.employee_enrollment_id,
            pay_period_start=data.pay_period_start,
            pay_period_end=data.pay_period_end,
            subscription_value=data.subscription_value,
            employer_subsidy=data.employer_subsidy,
            amount_deducted=max(amount, 0),
            deduction_scheduled_date=data.deduction_scheduled_date,
        )
        self.db.add(deduction)
        await self.db.commit()
        await self.db.refresh(deduction)
        return deduction

    async def get_deductions(self, user_id: uuid.UUID, enrollment_id: uuid.UUID | None = None) -> list[PayrollDeduction]:
        result = await self.db.execute(
            select(CorporatePartner).where(CorporatePartner.user_id == user_id)
        )
        partner = result.scalar_one_or_none()
        if not partner:
            return []

        query = select(PayrollDeduction).join(EmployeeEnrollment).where(
            EmployeeEnrollment.corporate_id == partner.id
        )
        if enrollment_id:
            query = query.where(PayrollDeduction.employee_enrollment_id == enrollment_id)

        result = await self.db.execute(query.order_by(PayrollDeduction.created_at.desc()))
        return list(result.scalars().all())

    async def mark_processed(self, user_id: uuid.UUID, deduction_id: uuid.UUID, external_ref: str | None = None) -> PayrollDeduction:
        deductions = await self.get_deductions(user_id)
        deduction = next((d for d in deductions if d.id == deduction_id), None)
        if not deduction:
            raise ValueError("Deduction not found")
        deduction.status = "processed"
        deduction.processed_at = datetime.now(timezone.utc)
        deduction.external_ref = external_ref
        await self.db.commit()
        await self.db.refresh(deduction)
        return deduction

    async def create_bulk_deductions(self, user_id: uuid.UUID, pay_period_start: date, pay_period_end: date, deduction_date: date) -> list[PayrollDeduction]:
        result = await self.db.execute(
            select(CorporatePartner).where(CorporatePartner.user_id == user_id)
        )
        partner = result.scalar_one_or_none()
        if not partner:
            raise ValueError("Corporate profile not found")

        result = await self.db.execute(
            select(EmployeeEnrollment).where(
                EmployeeEnrollment.corporate_id == partner.id,
                EmployeeEnrollment.is_active == True,
            )
        )
        employees = list(result.scalars().all())
        if not employees:
            raise ValueError("No active employees enrolled")

        deductions = []
        for emp in employees:
            subscription_value = partner.max_employee_benefit or 0
            subsidy = (subscription_value * (partner.subsidy_percentage or 0)) / 100
            amount = subscription_value - subsidy

            deduction = PayrollDeduction(
                employee_enrollment_id=emp.id,
                pay_period_start=pay_period_start,
                pay_period_end=pay_period_end,
                subscription_value=subscription_value,
                employer_subsidy=subsidy,
                amount_deducted=max(amount, 0),
                deduction_scheduled_date=deduction_date,
            )
            self.db.add(deduction)
            deductions.append(deduction)

        await self.db.commit()
        return deductions