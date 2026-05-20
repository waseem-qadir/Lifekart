from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal, engine
from app.modules.analytics.service import AnalyticsService


@celery_app.task(name="app.tasks.analytics_tasks.calculate_weekly_snapshot")
def calculate_weekly_snapshot():
    import asyncio

    async def _run():
        await engine.dispose()
        try:
            async with AsyncSessionLocal() as db:
                service = AnalyticsService(db)
                result = await service.calculate_full_platform_snapshot()
                return result
        finally:
            await engine.dispose()

    return asyncio.run(_run())