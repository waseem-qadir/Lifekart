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


class BulkDeductionRequest(BaseModel):
    pay_period_start: date
    pay_period_end: date
    deduction_date: date
    subscription_value: Decimal = Field(default=0, ge=0)