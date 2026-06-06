import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


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


class HealthTransitionCreate(BaseModel):
    health_profile_id: uuid.UUID
    transition_type: str = Field(pattern=r"^(condition_added|condition_removed|pregnancy|age_milestone)$")
    condition_name: str | None = Field(None, max_length=100)
    trigger_date: date
    affected_subscriptions: dict[str, list[str]] = Field(default_factory=dict)
    notes: str | None = None


class HealthTransitionResponse(BaseModel):
    id: uuid.UUID
    health_profile_id: uuid.UUID
    transition_type: str
    condition_name: str | None
    trigger_date: date
    affected_subscriptions: dict
    notes: str | None
    is_applied: bool
    created_at: datetime

    model_config = {"from_attributes": True}