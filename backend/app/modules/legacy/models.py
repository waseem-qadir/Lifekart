import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LegacyNominee(Base):
    __tablename__ = "legacy_nominees"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id"), nullable=False, index=True
    )
    nominee_name: Mapped[str] = mapped_column(String(255), nullable=False)
    nominee_relationship: Mapped[str] = mapped_column(String(30), nullable=False)
    nominee_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    nominee_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    nominee_aadhaar: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    household = relationship("Household", back_populates="nominees")
    legacy_activations = relationship(
        "LegacyActivation", back_populates="successor_nominee", foreign_keys="LegacyActivation.successor_nominee_id"
    )


class LegacyActivation(Base):
    __tablename__ = "legacy_activations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id"), nullable=False, index=True
    )
    original_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    successor_nominee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("legacy_nominees.id"), nullable=False, index=True
    )
    transfer_household_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id"), nullable=True, index=True
    )
    deceased_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    active_subscriptions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    transferred_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending_verification")
    death_certificate_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    activation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    successor_nominee = relationship(
        "LegacyNominee", back_populates="legacy_activations", foreign_keys=[successor_nominee_id]
    )