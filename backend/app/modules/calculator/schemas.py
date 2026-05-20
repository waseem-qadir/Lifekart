import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    household_id: uuid.UUID | None = None


class GenerateResponse(BaseModel):
    task_id: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict | None = None


class SubscriptionUpdate(BaseModel):
    quantity_per_delivery: float | None = Field(None, gt=0)
    frequency_days: int | None = Field(None, ge=1)
    # locked_unit_price: Decimal | None = Field(None, ge=0)
    # status: str | None = Field(None, pattern=r"^(active|paused|cancelled)$")


class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    household_id: uuid.UUID
    member_id: uuid.UUID | None
    product_id: uuid.UUID
    quantity_per_delivery: float
    frequency_days: int
    start_date: date
    end_date: date
    next_delivery_date: date
    status: str
    source: str
    locked_unit_price: Decimal
    price_ceiling_pct: Decimal | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}