from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import PlatformMetricsSnapshot
from app.modules.scheduling.models import DeliveryEvent
from app.modules.calculator.models import LifetimeSubscription
from app.modules.catalog.models import Product
from app.modules.corporate.models import CorporatePartner
from app.modules.profiling.models import Household
from app.modules.community.models import CommunityOrder


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_user_monthly_savings(self, household_id: str) -> dict:
        first_of_month = date.today().replace(day=1)

        result = await self.db.execute(
            select(
                func.coalesce(func.sum(DeliveryEvent.quantity * DeliveryEvent.unit_price_applied), 0).label("paid"),
                func.coalesce(func.count(DeliveryEvent.id), 0).label("delivery_count"),
            ).where(
                DeliveryEvent.household_id == household_id,
                DeliveryEvent.scheduled_date >= first_of_month,
                DeliveryEvent.scheduled_date <= date.today(),
                DeliveryEvent.status.in_(["pending", "delivered", "partially_filled"]),
            )
        )
        row = result.one()
        total_paid = Decimal(str(row.paid))
        delivery_count = int(row.delivery_count)

        result = await self.db.execute(
            select(func.sum(
                DeliveryEvent.quantity * Product.unit_price_retail
            )).select_from(DeliveryEvent).join(
                Product, DeliveryEvent.product_id == Product.id
            ).where(
                DeliveryEvent.household_id == household_id,
                DeliveryEvent.scheduled_date >= first_of_month,
                DeliveryEvent.scheduled_date <= date.today(),
                DeliveryEvent.status.in_(["pending", "delivered", "partially_filled"]),
            )
        )
        retail_equivalent = Decimal(str(result.scalar_one() or 0))

        monthly_savings = retail_equivalent - total_paid

        result = await self.db.execute(
            select(func.coalesce(func.sum(
                DeliveryEvent.quantity * (Product.unit_price_retail - DeliveryEvent.unit_price_applied)
            ), 0)).select_from(DeliveryEvent).join(
                Product, DeliveryEvent.product_id == Product.id
            ).where(
                DeliveryEvent.household_id == household_id,
                DeliveryEvent.status.in_(["pending", "delivered", "partially_filled"]),
            )
        )
        lifetime_savings = Decimal(str(result.scalar_one() or 0))

        result = await self.db.execute(
            select(func.count(LifetimeSubscription.id)).where(
                LifetimeSubscription.household_id == household_id,
                LifetimeSubscription.status == "active",
            )
        )
        active_subs = int(result.scalar_one())

        return {
            "monthly_savings": monthly_savings,
            "total_lifetime_savings": lifetime_savings,
            "active_subscriptions": active_subs,
            "deliveries_this_month": delivery_count,
            "period": f"{first_of_month} → {date.today()}",
        }

    async def calculate_full_platform_snapshot(self) -> dict:
        today = date.today()
        month_start = today.replace(day=1)
        month_end = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

        savings_result = await self.db.execute(
            select(
                func.count(Household.id.distinct()),
                func.coalesce(func.sum(
                    DeliveryEvent.quantity * (Product.unit_price_retail - DeliveryEvent.unit_price_applied)
                ), 0),
                func.coalesce(func.sum(
                    DeliveryEvent.quantity * Product.unit_price_retail
                ), 0),
            ).select_from(Household).join(
                DeliveryEvent, Household.id == DeliveryEvent.household_id, isouter=True
            ).join(
                Product, DeliveryEvent.product_id == Product.id, isouter=True
            ).where(
                func.coalesce(DeliveryEvent.scheduled_date, month_start) >= month_start,
                func.coalesce(DeliveryEvent.status, "").in_(["pending", "delivered", "partially_filled"]),
            )
        )
        row = savings_result.one()
        active_households = max(int(row[0]), 1)
        total_savings = Decimal(str(row[1]))
        retail_cost_avoided = Decimal(str(row[2]))
        avg_monthly = total_savings / active_households

        contracts_result = await self.db.execute(
            select(func.count(LifetimeSubscription.id)).where(
                LifetimeSubscription.status == "active",
            )
        )
        lifetime_contracts = int(contracts_result.scalar_one())

        corporate_result = await self.db.execute(
            select(func.count(CorporatePartner.id)).where(
                CorporatePartner.partnership_status == "active",
            )
        )
        corporate_partners = int(corporate_result.scalar_one())

        discount_result = await self.db.execute(
            select(
                func.coalesce(func.avg(CommunityOrder.wholesale_discount_achieved), 0)
            ).where(
                CommunityOrder.order_date >= month_start,
                CommunityOrder.status == "placed",
            )
        )
        avg_discount_pct = Decimal(str(discount_result.scalar_one() or 0))

        snapshot = PlatformMetricsSnapshot(
            avg_household_monthly_savings=avg_monthly,
            lifetime_contracts_signed=lifetime_contracts,
            active_employer_partnerships=corporate_partners,
            active_households=active_households,
            avg_wholesale_discount_pct=avg_discount_pct,
            retail_cost_avoided=retail_cost_avoided,
            extra_data={
                "total_savings_amount": str(total_savings),
                "active_households_sampled": active_households,
            },
            period_start=month_start,
            period_end=month_end,
        )
        self.db.add(snapshot)
        await self.db.commit()

        return {
            "avg_household_monthly_savings": avg_monthly,
            "lifetime_contracts_signed": lifetime_contracts,
            "active_employer_partnerships": corporate_partners,
            "avg_wholesale_discount_pct": avg_discount_pct,
            "retail_cost_avoided": retail_cost_avoided,
            "period": f"{month_start} → {month_end}",
        }

    async def get_latest_platform_kpi(self) -> dict | None:
        result = await self.db.execute(
            select(PlatformMetricsSnapshot)
            .order_by(PlatformMetricsSnapshot.recorded_at.desc())
            .limit(1)
        )
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            return None
        return {
            "avg_household_monthly_savings": snapshot.avg_household_monthly_savings,
            "lifetime_contracts_signed": snapshot.lifetime_contracts_signed,
            "active_employer_partnerships": snapshot.active_employer_partnerships,
            "avg_wholesale_discount_pct": snapshot.avg_wholesale_discount_pct,
            "retail_cost_avoided": snapshot.retail_cost_avoided,
            "period_start": str(snapshot.period_start or ""),
            "period_end": str(snapshot.period_end or ""),
            "recorded_at": snapshot.recorded_at.replace(tzinfo=None),
        }

    async def get_landing_page_stats(self) -> dict:
        from app.core.settings_loader import load_setting

        savings_config = await load_setting(self.db, "advertised_avg_monthly_savings")

        result = await self.db.execute(
            select(PlatformMetricsSnapshot)
            .order_by(PlatformMetricsSnapshot.recorded_at.desc())
            .limit(1)
        )
        snapshot = result.scalar_one_or_none()

        return {
            "advertised_avg_monthly_savings": Decimal(str(savings_config.get("amount", 5000))),
            "total_active_households": snapshot.active_households if snapshot else 0,
            "total_lifetime_contracts": snapshot.lifetime_contracts_signed if snapshot else 0,
            "total_corporate_partners": snapshot.active_employer_partnerships if snapshot else 0,
        }