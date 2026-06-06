import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GiftOrder(Base):
    __tablename__ = "gift_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    benefactor_household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id"), nullable=False, index=True
    )
    beneficiary_name: Mapped[str] = mapped_column(String(255), nullable=False)
    beneficiary_dob: Mapped[date] = mapped_column(Date, nullable=False)
    beneficiary_relationship: Mapped[str] = mapped_column(String(20), nullable=False)
    start_age: Mapped[int] = mapped_column(Integer, nullable=False)
    end_age: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    total_value_locked: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    benefactor_household = relationship("Household", back_populates="gift_orders", foreign_keys=[benefactor_household_id])
    items = relationship("GiftOrderItem", back_populates="gift_order")


class GiftOrderItem(Base):
    __tablename__ = "gift_order_items"
    __table_args__ = (
        Index("idx_gift_items_size_progression", "size_progression", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gift_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("gift_orders.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True
    )
    age_trigger: Mapped[int] = mapped_column(Integer, nullable=False)
    size_progression: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    locked_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    frequency_days: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_per_delivery: Mapped[float] = mapped_column(Float, nullable=False)

    gift_order = relationship("GiftOrder", back_populates="items")
    product = relationship("Product")