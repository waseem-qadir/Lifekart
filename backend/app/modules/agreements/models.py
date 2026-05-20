import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WholesaleAgreement(Base):
    __tablename__ = "wholesale_agreements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id"), nullable=False, index=True
    )
    manufacturer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manufacturers.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    price_ceiling_agreed: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    total_contract_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    household = relationship("Household", back_populates="agreements")
    manufacturer = relationship("Manufacturer", back_populates="agreements")
    items = relationship("AgreementItem", back_populates="agreement")


class AgreementItem(Base):
    __tablename__ = "agreement_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agreement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wholesale_agreements.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True
    )
    locked_unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    committed_monthly_qty: Mapped[float] = mapped_column(Float, nullable=False)
    frequency_days: Mapped[int] = mapped_column(Integer, nullable=False)
    total_item_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)

    agreement = relationship("WholesaleAgreement", back_populates="items")
    product = relationship("Product")