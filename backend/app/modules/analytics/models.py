import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PlatformMetricsSnapshot(Base):
    __tablename__ = "platform_metrics_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    avg_household_monthly_savings: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    lifetime_contracts_signed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active_employer_partnerships: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active_households: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    avg_wholesale_discount_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    retail_cost_avoided: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)

    extra_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)