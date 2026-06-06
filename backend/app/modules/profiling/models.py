import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Household(Base):
    __tablename__ = "households"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    lat: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    lng: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7), nullable=True)
    monthly_grocery_budget: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    prefer_organic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="household")
    members = relationship("Member", back_populates="household")
    subscriptions = relationship("LifetimeSubscription", back_populates="household")
    agreements = relationship("WholesaleAgreement", back_populates="household")
    gift_orders = relationship("GiftOrder", back_populates="benefactor_household", foreign_keys="GiftOrder.benefactor_household_id")
    community_memberships = relationship("CommunityMembership", back_populates="household")
    employee_enrollments = relationship("EmployeeEnrollment", back_populates="household")
    nominees = relationship("LegacyNominee", back_populates="household")


class Member(Base):
    __tablename__ = "members"
    __table_args__ = (
        Index("idx_members_lifestyle_tags", "lifestyle_tags", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id"), nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    family_relation: Mapped[str] = mapped_column("relation", String(30), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    dietary_preference: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    lifestyle_tags: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    household = relationship("Household", back_populates="members")
    subscriptions = relationship("LifetimeSubscription", back_populates="member")
    health_profile = relationship("HealthProfile", back_populates="member", uselist=False)