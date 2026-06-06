from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal, engine
from app.modules.health.service import HealthService
from app.modules.health.models import HealthTransition
from sqlalchemy import select


@celery_app.task(name="app.tasks.health_tasks.process_pending_transitions")
def process_pending_transitions():
    import asyncio

    async def _run():
        await engine.dispose()
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(HealthTransition).where(HealthTransition.is_applied == False)
                )
                pending = list(result.scalars().all())

                processed = []
                service = HealthService(db)

                for transition in pending:
                    try:
                        swaps = await service.process_transition(transition.id)
                        processed.append(swaps)
                    except Exception as e:
                        processed.append({"transition_id": str(transition.id), "error": str(e)})

                return {"processed_count": len(processed), "details": processed}
        finally:
            await engine.dispose()

    return asyncio.run(_run())