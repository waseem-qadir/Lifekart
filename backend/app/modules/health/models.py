import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class HealthProfile(Base):
    __tablename__ = "health_profiles"
    __table_args__ = (
        Index("idx_health_profiles_conditions", "existing_conditions", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.id"), nullable=False, index=True
    )
    blood_group: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    existing_conditions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    allergies: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    member = relationship("Member", back_populates="health_profile")
    transitions = relationship("HealthTransition", back_populates="health_profile")


class HealthTransition(Base):
    __tablename__ = "health_transitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    health_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("health_profiles.id"), nullable=False, index=True
    )
    transition_type: Mapped[str] = mapped_column(String(30), nullable=False)
    condition_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    trigger_date: Mapped[date] = mapped_column(Date, nullable=False)
    affected_subscriptions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    health_profile = relationship("HealthProfile", back_populates="transitions")


class HealthRule(Base):
    __tablename__ = "health_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    condition_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    forbidden_tags: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    required_tags: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    auto_apply: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())