from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal, engine
from app.core.settings_loader import load_settings
from app.modules.payroll.models import PayrollDeduction
from app.modules.corporate.models import CorporatePartner, EmployeeEnrollment
from app.modules.calculator.models import LifetimeSubscription
from sqlalchemy import select, func
from datetime import date, timedelta
from decimal import Decimal


@celery_app.task(name="app.tasks.payroll_tasks.generate_weekly_deductions")
def generate_weekly_deductions():
    import asyncio

    async def _run():
        await engine.dispose()
        try:
            async with AsyncSessionLocal() as db:
                config = await load_settings(db, [
                    "payroll_weeks_per_year",
                    "payroll_weeks_per_month",
                ])
                weeks_per_year = Decimal(str(config["payroll_weeks_per_year"]["weeks"]))
                weeks_per_month = Decimal(str(config["payroll_weeks_per_month"]["weeks"]))
                result = await db.execute(
                    select(CorporatePartner).where(CorporatePartner.partnership_status == "active")
                )
                partners = list(result.scalars().all())

                if not partners:
                    return {"deductions_created": 0, "reason": "no active partners"}

                partner_ids = [p.id for p in partners]

                result = await db.execute(
                    select(EmployeeEnrollment).where(
                        EmployeeEnrollment.corporate_id.in_(partner_ids),
                        EmployeeEnrollment.is_active == True,
                    )
                )
                enrollments = list(result.scalars().all())

                if not enrollments:
                    return {"deductions_created": 0, "reason": "no enrolled employees"}

                household_ids = [e.household_id for e in enrollments]
                employment_by_household = {e.household_id: e for e in enrollments}
                partner_by_id = {p.id: p for p in partners}

                result = await db.execute(
                    select(LifetimeSubscription).where(
                        LifetimeSubscription.household_id.in_(household_ids),
                        LifetimeSubscription.status == "active",
                    )
                )
                all_subs = list(result.scalars().all())

                subs_by_household: dict = {}
                for sub in all_subs:
                    subs_by_household.setdefault(sub.household_id, []).append(sub)

                total_created = 0
                today = date.today()
                week_start = today - timedelta(days=today.weekday())
                week_end = week_start + timedelta(days=6)

                for household_id, subs in subs_by_household.items():
                    enrollment = employment_by_household.get(household_id)
                    if not enrollment:
                        continue

                    partner = partner_by_id.get(enrollment.corporate_id)
                    if not partner:
                        continue

                    total_annual = Decimal("0")
                    for sub in subs:
                        deliveries_per_year = Decimal(str(365 / sub.frequency_days))
                        annual_cost = sub.locked_unit_price * Decimal(str(sub.quantity_per_delivery)) * deliveries_per_year
                        total_annual += annual_cost

                    weekly_amortized = total_annual / weeks_per_year

                    subsidy_pct = float(partner.subsidy_percentage or 0)
                    max_weekly = float(partner.max_employee_benefit or 0) / float(weeks_per_month)
                    capped_weekly = min(float(weekly_amortized), max_weekly) if max_weekly > 0 else float(weekly_amortized)
                    subsidy = capped_weekly * (subsidy_pct / 100)
                    amount = capped_weekly - subsidy

                    if amount <= 0:
                        continue

                    deduction = PayrollDeduction(
                        employee_enrollment_id=enrollment.id,
                        pay_period_start=week_start,
                        pay_period_end=week_end,
                        subscription_value=Decimal(str(capped_weekly)),
                        employer_subsidy=Decimal(str(subsidy)),
                        amount_deducted=Decimal(str(max(amount, 0))),
                        deduction_scheduled_date=week_end,
                    )
                    db.add(deduction)
                    total_created += 1

                await db.commit()
                return {"deductions_created": total_created, "week": f"{week_start} → {week_end}", "method": "amortized"}
        finally:
            await engine.dispose()

    return asyncio.run(_run())