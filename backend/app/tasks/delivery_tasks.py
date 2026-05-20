from datetime import date, timedelta

from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal, engine
from app.modules.calculator.models import LifetimeSubscription
from app.modules.scheduling.models import DeliveryEvent


@celery_app.task(name="app.tasks.delivery_tasks.process_daily_deliveries")
def process_daily_deliveries():
    import asyncio

    async def _run():
        await engine.dispose()
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(LifetimeSubscription)
                    .options(
                        joinedload(LifetimeSubscription.product),
                        joinedload(LifetimeSubscription.household),
                    )
                    .where(
                        LifetimeSubscription.status == "active",
                        LifetimeSubscription.start_date <= func.current_date(),
                        LifetimeSubscription.end_date >= func.current_date(),
                        LifetimeSubscription.next_delivery_date == func.current_date(),
                    )
                )
                subscriptions = result.unique().scalars().all()

                count = 0
                partial = 0
                skipped = 0

                for sub in subscriptions:
                    product = sub.product
                    if not product or not product.is_active or product.stock_quantity <= 0:
                        skipped += 1
                        continue

                    requested = float(sub.quantity_per_delivery)
                    available = float(product.stock_quantity)

                    if requested > available:
                        filled = available
                        status = "partially_filled"
                        partial += 1
                    else:
                        filled = requested
                        status = "pending"

                    product.stock_quantity -= filled

                    household = sub.household
                    address = {
                        "line1": household.address_line1,
                        "line2": household.address_line2,
                        "city": household.city,
                        "state": household.state,
                        "pincode": household.pincode,
                    } if household else {}

                    delivery = DeliveryEvent(
                        subscription_id=sub.id,
                        household_id=sub.household_id,
                        product_id=sub.product_id,
                        scheduled_date=date.today(),
                        quantity=filled,
                        unit_price_applied=sub.locked_unit_price,
                        status=status,
                        delivery_address=address,
                        notes="Partial fill: shipped {} of {} units".format(filled, requested)
                        if status == "partially_filled" else None,
                    )
                    db.add(delivery)

                    if status == "pending":
                        sub.next_delivery_date = sub.next_delivery_date + timedelta(days=sub.frequency_days)
                        count += 1

                await db.commit()
                return {
                    "processed": count,
                    "partial": partial,
                    "skipped": skipped,
                    "date": str(date.today()),
                }
        finally:
            await engine.dispose()

    return asyncio.run(_run())


@celery_app.task(name="app.tasks.delivery_tasks.generate_monthly_invoices")
def generate_monthly_invoices():
    import asyncio

    async def _run():
        await engine.dispose()
        try:
            from app.modules.payments.service import PaymentsService
            async with AsyncSessionLocal() as db:
                service = PaymentsService(db)
                result = await service.generate_invoices_for_all()
                return result
        finally:
            await engine.dispose()

    return asyncio.run(_run())


@celery_app.task(name="app.tasks.delivery_tasks.archive_old_deliveries")
def archive_old_deliveries():
    import asyncio

    async def _run():
        await engine.dispose()
        try:
            async with AsyncSessionLocal() as db:
                cutoff = date.today() - timedelta(days=30)
                result = await db.execute(
                    select(DeliveryEvent).where(
                        DeliveryEvent.scheduled_date < cutoff,
                        DeliveryEvent.status.in_(["delivered", "failed", "returned"]),
                    )
                )
                old_events = result.scalars().all()
                count = len(old_events)
                for event in old_events:
                    await db.delete(event)
                await db.commit()
                return {"archived": count}
        finally:
            await engine.dispose()

    return asyncio.run(_run())