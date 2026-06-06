import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PaymentMethodCreate(BaseModel):
    stripe_payment_method_id: str = Field(min_length=5)


class PaymentMethodResponse(BaseModel):
    id: uuid.UUID
    household_id: uuid.UUID
    stripe_payment_method_id: str
    type: str
    brand: str | None
    last_four: str | None
    exp_month: int | None
    exp_year: int | None
    is_default: bool

    model_config = {"from_attributes": True}


class InvoiceLineItem(BaseModel):
    product_name: str
    quantity: float
    unit_price: Decimal
    total: Decimal


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    household_id: uuid.UUID
    stripe_invoice_id: str | None
    hosted_invoice_url: str | None = None
    invoice_pdf: str | None = None
    amount_total: Decimal
    amount_paid: Decimal | None
    currency: str
    status: str
    issued_at: datetime
    paid_at: datetime | None
    billing_period_start: date
    billing_period_end: date
    line_items: list[InvoiceLineItem] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class PaymentTransactionResponse(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    stripe_payment_intent_id: str | None
    amount: Decimal
    currency: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}