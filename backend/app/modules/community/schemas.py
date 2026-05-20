import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


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
    admin_household_id: uuid.UUID
    min_households_for_pooling: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CommunityMembershipResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    household_id: uuid.UUID
    joined_at: datetime

    model_config = {"from_attributes": True}


class CommunityOrderResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    product_id: uuid.UUID
    total_quantity: float
    per_household_share: float
    contributing_households: int
    discounted_unit_price: Decimal | None
    wholesale_discount_achieved: Decimal | None
    status: str
    order_date: datetime

    model_config = {"from_attributes": True}