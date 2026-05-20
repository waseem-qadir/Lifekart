from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal, engine
from app.modules.price_protect.service import PriceProtectionService


@celery_app.task(name="app.tasks.price_monitor.check_price_ceilings")
def check_price_ceilings():
    import asyncio

    async def _run():
        await engine.dispose()
        try:
            async with AsyncSessionLocal() as db:
                service = PriceProtectionService(db)
                alerts = await service.check_ceiling_breaches()
                return {"alerts_created": len(alerts), "alerts": alerts}
        finally:
            await engine.dispose()

    return asyncio.run(_run())


@celery_app.task(name="app.tasks.price_monitor.check_stock_availability")
def check_stock_availability():
    import asyncio

    async def _run():
        await engine.dispose()
        try:
            async with AsyncSessionLocal() as db:
                service = PriceProtectionService(db)
                swaps = await service.check_stock_and_substitute()
                return {"products_swapped": len(swaps), "swaps": swaps}
        finally:
            await engine.dispose()

    return asyncio.run(_run())