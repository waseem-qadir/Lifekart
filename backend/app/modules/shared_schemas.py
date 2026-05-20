import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PayrollDeductionCreate(BaseModel):
    employee_enrollment_id: uuid.UUID
    pay_period_start: date
    pay_period_end: date
    subscription_value: Decimal = Field(ge=0)
    employer_subsidy: Decimal = Field(ge=0)
    deduction_scheduled_date: date


class PayrollDeductionResponse(BaseModel):
    id: uuid.UUID
    employee_enrollment_id: uuid.UUID
    pay_period_start: date
    pay_period_end: date
    subscription_value: Decimal
    employer_subsidy: Decimal
    amount_deducted: Decimal
    status: str
    deduction_scheduled_date: date
    processed_at: datetime | None
    external_ref: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CommunityGroupCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    locality: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    pincode: str | None = Field(None, max_length=10)
    min_households_for_pooling: int = Field(default=100, ge=10)


class CommunityGroupResponse(BaseModel):
    id: uuid.UUID
    name: str
    locality: str | None
    city: str | None
    state: str | None
    pincode: str | None
    min_households_for_pooling: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CommunityOrderResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    product_id: uuid.UUID
    total_quantity: float
    wholesale_discount_achieved: Decimal | None
    status: str
    order_date: date

    model_config = {"from_attributes": True}


class HealthTransitionCreate(BaseModel):
    health_profile_id: uuid.UUID
    transition_type: str = Field(pattern=r"^(condition_added|condition_removed|pregnancy|age_milestone)$")
    condition_name: str | None = Field(None, max_length=100)
    trigger_date: date
    affected_subscriptions: dict = Field(default_factory=dict)
    notes: str | None = None


class HealthTransitionResponse(BaseModel):
    id: uuid.UUID
    health_profile_id: uuid.UUID
    transition_type: str
    condition_name: str | None
    trigger_date: date
    affected_subscriptions: dict
    is_applied: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class HealthProfileResponse(BaseModel):
    id: uuid.UUID
    member_id: uuid.UUID
    blood_group: str | None
    height_cm: float | None
    weight_kg: float | None
    existing_conditions: list
    allergies: list

    model_config = {"from_attributes": True}


class HealthProfileUpdate(BaseModel):
    blood_group: str | None = None
    height_cm: float | None = Field(None, ge=0)
    weight_kg: float | None = Field(None, ge=0)
    existing_conditions: list | None = None
    allergies: list | None = None


class LegacyNomineeCreate(BaseModel):
    nominee_name: str = Field(min_length=2, max_length=255)
    nominee_relationship: str = Field(pattern=r"^(spouse|child|parent|sibling)$")
    nominee_phone: str | None = Field(None, min_length=10, max_length=20)
    nominee_email: str | None = Field(None, max_length=255)
    nominee_aadhaar: str | None = Field(None, min_length=12, max_length=12)


class LegacyNomineeResponse(BaseModel):
    id: uuid.UUID
    household_id: uuid.UUID
    nominee_name: str
    nominee_relationship: str
    nominee_phone: str | None
    nominee_email: str | None
    is_primary: bool
    created_at: datetime

    model_config = {"from_attributes": True}