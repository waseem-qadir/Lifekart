import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DeliveryEvent(Base):
    __tablename__ = "delivery_events"
    __table_args__ = (
        UniqueConstraint("subscription_id", "scheduled_date", name="uq_delivery_subscription_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lifetime_subscriptions.id"), nullable=False, index=True
    )
    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True
    )
    scheduled_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    actual_delivery_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit_price_applied: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    delivery_address: Mapped[dict] = mapped_column(JSONB, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    subscription = relationship("LifetimeSubscription", back_populates="delivery_events")
    product = relationship("Product")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True
    )
    wholesale_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    retail_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product")


class PriceProtectionRule(Base):
    __tablename__ = "price_protection_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True
    )
    ceiling_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    max_annual_increase_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    effective_from: Mapped[datetime] = mapped_column(Date, nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product")


class SubstitutionEvent(Base):
    __tablename__ = "substitution_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lifetime_subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lifetime_subscriptions.id"), nullable=False, index=True
    )
    original_product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True
    )
    substituted_product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True
    )
    substituted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reason: Mapped[str] = mapped_column(String(30), nullable=False)
    substitution_type: Mapped[str] = mapped_column(String(20), nullable=False, default="TEMPORARY")
    is_user_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    subscription = relationship(
        "LifetimeSubscription", back_populates="substitution_events", foreign_keys=[lifetime_subscription_id]
    )
    original_product = relationship("Product", foreign_keys=[original_product_id])
    substituted_product = relationship("Product", foreign_keys=[substituted_product_id])


class PriceCeilingAlert(Base):
    __tablename__ = "price_ceiling_alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True
    )
    current_catalog_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    locked_ceiling: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    affected_households: Mapped[int] = mapped_column(Integer, nullable=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product")