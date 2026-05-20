import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class MemberCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    family_relation: str = Field(min_length=1, max_length=30)
    date_of_birth: date
    gender: str | None = Field(None, pattern=r"^(male|female|other)$")
    dietary_preference: str | None = Field(
        None, pattern=r"^(vegetarian|non_veg|vegan|jain|keto|diabetic)$"
    )
    lifestyle_tags: list[str] = Field(default_factory=list)

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v


class MemberUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=255)
    gender: str | None = Field(None, pattern=r"^(male|female|other)$")
    dietary_preference: str | None = Field(
        None, pattern=r"^(vegetarian|non_veg|vegan|jain|keto|diabetic)$"
    )
    lifestyle_tags: list[str] | None = None
    is_active: bool | None = None


class MemberResponse(BaseModel):
    id: uuid.UUID
    household_id: uuid.UUID
    full_name: str
    family_relation: str
    date_of_birth: date
    gender: str | None
    dietary_preference: str | None
    lifestyle_tags: list
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HouseholdCreate(BaseModel):
    address_line1: str = Field(max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str = Field(max_length=100)
    state: str = Field(max_length=100)
    pincode: str = Field(max_length=10)
    lat: Decimal | None = None
    lng: Decimal | None = None
    monthly_grocery_budget: Decimal | None = Field(None, ge=0)
    prefer_organic: bool = False
    members: list[MemberCreate] = Field(default_factory=list, max_length=20)


class HouseholdUpdate(BaseModel):
    address_line1: str | None = Field(None, max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    pincode: str | None = Field(None, max_length=10)
    lat: Decimal | None = None
    lng: Decimal | None = None
    monthly_grocery_budget: Decimal | None = Field(None, ge=0)
    prefer_organic: bool | None = None


class HouseholdResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    address_line1: str | None
    address_line2: str | None
    city: str | None
    state: str | None
    pincode: str | None
    lat: Decimal | None
    lng: Decimal | None
    monthly_grocery_budget: Decimal | None
    prefer_organic: bool
    created_at: datetime
    updated_at: datetime
    members: list[MemberResponse] = []

    model_config = {"from_attributes": True}