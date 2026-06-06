from sqlalchemy import text

from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal, engine
from app.core.settings_loader import load_settings


@celery_app.task(name="app.tasks.catalog_tasks.rebuild_all_substitutes")
def rebuild_all_substitutes():
    import asyncio

    async def _run():
        await engine.dispose()
        try:
            async with AsyncSessionLocal() as db:
                config = await load_settings(db, [
                    "substitute_price_tolerance_pct",
                    "substitute_max_alternatives",
                ])
                tolerance = config["substitute_price_tolerance_pct"]["pct"] / 100.0
                max_alt = int(config["substitute_max_alternatives"]["count"])

                await db.execute(text("DELETE FROM product_substitutes"))

                await db.execute(text("""
                    INSERT INTO product_substitutes (id, product_id, substitute_product_id, priority_rank, created_at, updated_at)
                    SELECT
                        gen_random_uuid(),
                        product_id,
                        substitute_product_id,
                        priority_rank,
                        NOW(),
                        NOW()
                    FROM (
                        SELECT
                            p1.id AS product_id,
                            p2.id AS substitute_product_id,
                            ROW_NUMBER() OVER (
                                PARTITION BY p1.id
                                ORDER BY ABS(p1.unit_price_wholesale - p2.unit_price_wholesale) ASC
                            ) AS priority_rank
                        FROM products p1
                        JOIN products p2
                            ON p1.category_id = p2.category_id
                            AND p1.id != p2.id
                        WHERE p1.is_active = true
                          AND p2.is_active = true
                          AND p2.stock_quantity > 0
                          AND p1.unit_price_wholesale > 0
                          AND (ABS(p1.unit_price_wholesale - p2.unit_price_wholesale) / p1.unit_price_wholesale) <= :tolerance
                    ) ranked
                    WHERE priority_rank <= :max_alt;
                """), {"tolerance": tolerance, "max_alt": max_alt})

                await db.commit()

                result = await db.execute(text("SELECT count(*) FROM product_substitutes"))
                count = result.scalar_one()

                return {"status": "success", "substitutes_created": count, "tolerance_pct": tolerance * 100, "max_per_product": max_alt}
        finally:
            await engine.dispose()

    return asyncio.run(_run())