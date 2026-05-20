import uuid
from datetime import date, datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field, model_validator


class AgreementItemCreate(BaseModel):
    product_id: uuid.UUID
    locked_unit_price: Decimal = Field(ge=0)
    committed_monthly_qty: float = Field(gt=0)
    frequency_days: int = Field(ge=1)


class AgreementItemUpdate(BaseModel):
    locked_unit_price: Decimal | None = Field(None, ge=0)
    committed_monthly_qty: float | None = Field(None, gt=0)
    frequency_days: int | None = Field(None, ge=1)


class AgreementItemResponse(BaseModel):
    id: uuid.UUID
    agreement_id: uuid.UUID
    product_id: uuid.UUID
    locked_unit_price: Decimal
    committed_monthly_qty: float
    frequency_days: int
    total_item_value: Decimal | None

    model_config = {"from_attributes": True}


class AgreementCreate(BaseModel):
    manufacturer_id: uuid.UUID
    start_date: date
    end_date: date
    price_ceiling_agreed: Decimal | None = Field(None, ge=0, le=100)
    items: list[AgreementItemCreate] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def dates_must_be_valid(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")

        from app.core.config import settings
        exact_60_years = self.start_date + relativedelta(years=settings.MAX_LIFETIME_YEARS)

        if self.end_date != exact_60_years:
            raise ValueError(
                f"LifeKart agreements require an exact {settings.MAX_LIFETIME_YEARS}-year lock-in. "
                f"For start_date {self.start_date}, end_date must be {exact_60_years}"
            )

        return self


class AgreementUpdate(BaseModel):
    status: str | None = Field(None, pattern=r"^(active|cancelled)$")
    price_ceiling_agreed: Decimal | None = Field(None, ge=0, le=100)


class AgreementResponse(BaseModel):
    id: uuid.UUID
    household_id: uuid.UUID
    manufacturer_id: uuid.UUID
    status: str
    start_date: date
    end_date: date
    price_ceiling_agreed: Decimal | None
    total_contract_value: Decimal | None
    signed_at: datetime | None
    cancelled_at: datetime | None
    cancellation_reason: str | None
    created_at: datetime
    updated_at: datetime
    items: list[AgreementItemResponse] = []

    model_config = {"from_attributes": True}