from datetime import date, timedelta

from sqlalchemy import func, select

from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal, engine
from app.core.settings_loader import load_settings
from app.modules.community.models import CommunityGroup, CommunityMembership, CommunityOrder
from app.modules.calculator.models import LifetimeSubscription
from app.modules.catalog.models import Product


def _calculate_discount(total_qty: float, tiers: list[dict]) -> float:
    discount = 0.0
    for tier in tiers:
        if total_qty >= tier["threshold"]:
            discount = tier["discount_pct"]
    return discount


@celery_app.task(name="app.tasks.community_tasks.aggregate_orders")
def aggregate_community_orders():
    import asyncio

    async def _run():
        await engine.dispose()
        try:
            async with AsyncSessionLocal() as db:
                config = await load_settings(db, ["community_discount_tiers"])
                dc_tiers = config["community_discount_tiers"]["tiers"]

                tomorrow = date.today() + timedelta(days=1)

                active_groups_result = await db.execute(
                    select(CommunityGroup).where(CommunityGroup.status == "active")
                )
                active_groups = list(active_groups_result.scalars().all())

                if not active_groups:
                    return {"groups_processed": 0, "orders_created": 0}

                created = 0

                for group in active_groups:
                    members_result = await db.execute(
                        select(CommunityMembership.household_id).where(
                            CommunityMembership.group_id == group.id
                        )
                    )
                    household_ids = [row[0] for row in members_result.fetchall()]

                    if not household_ids:
                        continue

                    subscriptions_result = await db.execute(
                        select(
                            LifetimeSubscription.product_id,
                            func.sum(LifetimeSubscription.quantity_per_delivery).label("total_qty"),
                            func.count(LifetimeSubscription.household_id.distinct()).label("num_households"),
                        )
                        .where(
                            LifetimeSubscription.household_id.in_(household_ids),
                            LifetimeSubscription.status == "active",
                            LifetimeSubscription.next_delivery_date == tomorrow,
                        )
                        .group_by(LifetimeSubscription.product_id)
                    )
                    product_aggregates = subscriptions_result.fetchall()

                    for product_id, total_qty, num_households in product_aggregates:
                        if total_qty <= 0:
                            continue

                        discount_pct = _calculate_discount(total_qty, dc_tiers)

                        product_result = await db.execute(
                            select(Product).where(Product.id == product_id)
                        )
                        product = product_result.scalar_one_or_none()
                        if not product:
                            continue

                        discounted_price = product.unit_price_wholesale * (1 - discount_pct / 100)
                        per_share = total_qty / num_households if num_households > 0 else 0

                        order = CommunityOrder(
                            group_id=group.id,
                            product_id=product_id,
                            total_quantity=float(total_qty),
                            per_household_share=per_share,
                            contributing_households=num_households,
                            discounted_unit_price=discounted_price,
                            wholesale_discount_achieved=discount_pct,
                            status="placed",
                            order_date=tomorrow,
                        )
                        db.add(order)
                        created += 1

                await db.commit()
                return {"groups_processed": len(active_groups), "orders_created": created}
        finally:
            await engine.dispose()

    return asyncio.run(_run())