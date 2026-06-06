import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class GiftOrderItemCreate(BaseModel):
    product_id: uuid.UUID
    age_trigger: int = Field(ge=0)
    size_progression: dict[str, str] = Field(default_factory=dict)
    frequency_days: int = Field(ge=1)
    quantity_per_delivery: float = Field(gt=0)


class GiftOrderCreate(BaseModel):
    beneficiary_name: str = Field(min_length=2, max_length=255)
    beneficiary_dob: date
    beneficiary_relationship: str = Field(
        pattern=r"^(child|grandchild|niece|nephew)$"
    )
    end_age: int = Field(ge=1)
    items: list[GiftOrderItemCreate] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def start_before_end(self):
        from app.core.config import settings
        if self.end_age > settings.MAX_LIFETIME_YEARS:
            raise ValueError(f"end_age cannot exceed {settings.MAX_LIFETIME_YEARS} years")
        for item in self.items:
            if item.age_trigger >= self.end_age:
                raise ValueError(
                    f"age_trigger ({item.age_trigger}) must be less than end_age ({self.end_age})"
                )
        return self


class GiftOrderItemResponse(BaseModel):
    id: uuid.UUID
    gift_order_id: uuid.UUID
    product_id: uuid.UUID
    age_trigger: int
    size_progression: dict
    locked_price: Decimal
    frequency_days: int
    quantity_per_delivery: float

    model_config = {"from_attributes": True}


class GiftOrderResponse(BaseModel):
    id: uuid.UUID
    benefactor_household_id: uuid.UUID
    beneficiary_name: str
    beneficiary_dob: date
    beneficiary_relationship: str
    start_age: int
    end_age: int
    status: str
    total_value_locked: Decimal | None
    payment_status: str
    created_at: datetime
    items: list[GiftOrderItemResponse] = []

    model_config = {"from_attributes": True}