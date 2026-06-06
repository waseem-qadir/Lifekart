import json
import logging
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal, engine
from app.modules.calculator.models import LifetimeSubscription
from app.modules.agreements.models import AgreementItem
from app.core.settings_model import SystemSetting, DEFAULTS

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.business_tasks.enforce_grace_periods")
def enforce_grace_periods():
    import asyncio

    async def _run():
        await engine.dispose()
        try:
            async with AsyncSessionLocal() as db:
                # Fetch global grace period setting
                result = await db.execute(select(SystemSetting).where(SystemSetting.key == "default_grace_period_days"))
                setting = result.scalar_one_or_none()
                grace_period_days = setting.value.get("days", DEFAULTS["default_grace_period_days"]["days"]) if setting else DEFAULTS["default_grace_period_days"]["days"]

                # Find all paused subscriptions older than grace period
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=grace_period_days)
                
                result = await db.execute(
                    select(LifetimeSubscription)
                    .where(LifetimeSubscription.status == "paused")
                    .where(LifetimeSubscription.paused_at < cutoff_date)
                )
                breached_subs = result.scalars().all()
                
                for sub in breached_subs:
                    sub.status = "contract_breached"
                
                await db.commit()
                logger.info(f"Enforced grace period on {len(breached_subs)} subscriptions.")
                return {"breached_contracts": len(breached_subs)}
        finally:
            await engine.dispose()

    return asyncio.run(_run())

@celery_app.task(name="app.tasks.business_tasks.generate_manufacturer_forecast")
def generate_manufacturer_forecast():
    import asyncio

    async def _run():
        await engine.dispose()
        try:
            async with AsyncSessionLocal() as db:
                # Group all AgreementItem rows by manufacturer and product, sum committed qty
                # We need to join AgreementItem -> WholesaleAgreement to ensure it's active
                # and AgreementItem -> Product to get manufacturer_id
                from app.modules.agreements.models import WholesaleAgreement
                from app.modules.catalog.models import Product

                result = await db.execute(
                    select(
                        Product.manufacturer_id,
                        AgreementItem.product_id,
                        func.sum(AgreementItem.committed_monthly_qty).label("total_monthly_qty")
                    )
                    .join(WholesaleAgreement, WholesaleAgreement.id == AgreementItem.agreement_id)
                    .join(Product, Product.id == AgreementItem.product_id)
                    .where(WholesaleAgreement.status == "active")
                    .group_by(Product.manufacturer_id, AgreementItem.product_id)
                )
                
                forecast_data = []
                historical_pause_rate = 0.04  # Subtract 4% for grace period users
                
                for row in result.all():
                    manufacturer_id, product_id, total_monthly_qty = row
                    adjusted_qty = float(total_monthly_qty) * (1 - historical_pause_rate)
                    
                    forecast_data.append({
                        "manufacturer_id": str(manufacturer_id),
                        "product_id": str(product_id),
                        "30_day_forecast": round(adjusted_qty, 2),
                        "90_day_forecast": round(adjusted_qty * 3, 2)
                    })
                
                # Mock generating a report
                os.makedirs("forecast_reports", exist_ok=True)
                report_path = f"forecast_reports/forecast_{datetime.now().strftime('%Y_%m_%d')}.json"
                with open(report_path, "w") as f:
                    json.dump(forecast_data, f, indent=2)
                
                logger.info(f"Generated 90-day forecast report for {len(forecast_data)} products at {report_path}")
                return {"report_path": report_path, "products_forecasted": len(forecast_data)}
        finally:
            await engine.dispose()

    return asyncio.run(_run())
