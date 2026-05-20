from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Import all models upfront to ensure SQLAlchemy relationships are registered
# before Celery loads task modules
from app.db.base import Base
import app.modules.users.models
import app.modules.catalog.models
import app.modules.profiling.models
import app.modules.calculator.models
import app.modules.health.models
import app.modules.agreements.models
import app.modules.scheduling.models
import app.modules.payments.models
import app.modules.gifting.models
import app.modules.corporate.models
import app.modules.payroll.models
import app.modules.community.models
import app.modules.legacy.models
import app.modules.analytics.models

celery_app = Celery(
    "lifekart",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.calculator_tasks",
        "app.tasks.catalog_tasks",
        "app.tasks.analytics_tasks",
        "app.tasks.community_tasks",
        "app.tasks.delivery_tasks",
        "app.tasks.price_monitor",
        "app.tasks.payroll_tasks",
        "app.tasks.health_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
    task_soft_time_limit=540,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    "process-health-transitions": {
        "task": "app.tasks.health_tasks.process_pending_transitions",
        "schedule": crontab(hour=1, minute=0),
    },
    "check-stock-availability": {
        "task": "app.tasks.price_monitor.check_stock_availability",
        "schedule": crontab(hour=1, minute=30),
    },
    "process-daily-deliveries": {
        "task": "app.tasks.delivery_tasks.process_daily_deliveries",
        "schedule": crontab(hour=2, minute=0),
    },
    "archive-old-deliveries": {
        "task": "app.tasks.delivery_tasks.archive_old_deliveries",
        "schedule": crontab(hour=3, minute=0),
    },
    "generate-monthly-invoices": {
        "task": "app.tasks.delivery_tasks.generate_monthly_invoices",
        "schedule": crontab(hour=1, minute=0, day_of_month=1),
    },
    "monitor-price-ceilings": {
        "task": "app.tasks.price_monitor.check_price_ceilings",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),
    },
    "generate-weekly-payroll-deductions": {
        "task": "app.tasks.payroll_tasks.generate_weekly_deductions",
        "schedule": crontab(hour=0, minute=30, day_of_week=1),
    },
    "aggregate-community-orders": {
        "task": "app.tasks.community_tasks.aggregate_orders",
        "schedule": crontab(hour=23, minute=0),
    },
    "rebuild-product-substitutes": {
        "task": "app.tasks.catalog_tasks.rebuild_all_substitutes",
        "schedule": crontab(hour=4, minute=0),
    },
    "calculate-weekly-platform-snapshot": {
        "task": "app.tasks.analytics_tasks.calculate_weekly_snapshot",
        "schedule": crontab(hour=0, minute=0, day_of_week=0),
    },
}