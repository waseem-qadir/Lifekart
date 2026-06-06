import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PriceProtectionRuleCreate(BaseModel):
    product_id: uuid.UUID
    ceiling_price: Decimal = Field(ge=0)
    max_annual_increase_pct: Decimal = Field(ge=0, le=100, default=0)
    effective_from: date
    effective_to: date | None = None


class PriceProtectionRuleResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    ceiling_price: Decimal
    max_annual_increase_pct: Decimal
    effective_from: date
    effective_to: date | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PriceHistoryResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    wholesale_price: Decimal
    retail_price: Decimal
    recorded_at: datetime

    model_config = {"from_attributes": True}


class SubstitutionEventCreate(BaseModel):
    lifetime_subscription_id: uuid.UUID
    substitute_product_id: uuid.UUID
    reason: str = Field(pattern=r"^(discontinued|out_of_stock|quality_issue|price_ceiling_breach)$")
    substitution_type: str = "TEMPORARY"


class SubstitutionEventResponse(BaseModel):
    id: uuid.UUID
    lifetime_subscription_id: uuid.UUID
    original_product_id: uuid.UUID
    substituted_product_id: uuid.UUID
    reason: str
    substitution_type: str
    substituted_at: datetime
    is_user_approved: bool

    model_config = {"from_attributes": True}