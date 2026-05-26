import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=255)
    icon: str | None = Field(None, max_length=50)
    unit_type: str = Field(min_length=1, max_length=20)
    avg_lifetime_consumption_per_year: float | None = None
    description: str | None = None
    image_url: str | None = None
    avg_savings: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    slug: str | None = Field(None, min_length=2, max_length=255)
    icon: str | None = Field(None, max_length=50)
    unit_type: str | None = Field(None, min_length=1, max_length=20)
    avg_lifetime_consumption_per_year: float | None = None
    description: str | None = None
    image_url: str | None = None
    avg_savings: str | None = None


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    icon: str | None
    unit_type: str
    avg_lifetime_consumption_per_year: float | None
    description: str | None = None
    image_url: str | None = None
    avg_savings: str | None = None
    productCount: int = Field(default=0, alias="product_count")
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


# ── Manufacturers ──

class ManufacturerCreate(BaseModel):
    company_name: str = Field(min_length=2, max_length=255)
    gstin: str | None = Field(None, min_length=10, max_length=20)
    address_line1: str | None = Field(None, max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    pincode: str | None = Field(None, max_length=10)
    contact_email: str | None = Field(None, max_length=255)


class ManufacturerUpdate(BaseModel):
    company_name: str | None = Field(None, min_length=2, max_length=255)
    gstin: str | None = Field(None, min_length=10, max_length=20)
    address_line1: str | None = Field(None, max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    pincode: str | None = Field(None, max_length=10)
    contact_email: str | None = Field(None, max_length=255)


class ManufacturerResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    company_name: str
    gstin: str | None
    address_line1: str | None
    address_line2: str | None
    city: str | None
    state: str | None
    pincode: str | None
    contact_email: str | None
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Products ──

class ProductCreate(BaseModel):
    category_id: uuid.UUID
    name: str = Field(min_length=2, max_length=255)
    sku: str = Field(min_length=2, max_length=100)
    image_url: str | None = Field(None, max_length=500)
    unit_size: str | None = Field(None, max_length=50)
    unit_price_wholesale: Decimal = Field(ge=0)
    unit_price_retail: Decimal = Field(ge=0)
    min_order_quantity: float = Field(default=1, ge=0)
    max_order_quantity: float | None = None
    stock_quantity: float = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    image_url: str | None = Field(None, max_length=500)
    unit_size: str | None = Field(None, max_length=50)
    unit_price_wholesale: Decimal | None = Field(None, ge=0)
    unit_price_retail: Decimal | None = Field(None, ge=0)
    min_order_quantity: float | None = Field(None, ge=0)
    max_order_quantity: float | None = None
    stock_quantity: float | None = Field(None, ge=0)
    is_active: bool | None = None


class ProductResponse(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    manufacturer_id: uuid.UUID
    name: str
    sku: str
    image_url: str | None
    unit_size: str | None
    unit_price_wholesale: Decimal
    unit_price_retail: Decimal
    min_order_quantity: float
    max_order_quantity: float | None
    stock_quantity: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Product Substitutes ──

class SubstitutionCreate(BaseModel):
    product_id: uuid.UUID
    substitute_product_id: uuid.UUID
    priority_rank: int = Field(ge=1)


class SubstitutionResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    substitute_product_id: uuid.UUID
    priority_rank: int

    model_config = {"from_attributes": True}


# ── Product Progression Rules ──

class ProgressionRuleCreate(BaseModel):
    category_id: uuid.UUID
    specific_product_id: uuid.UUID
    start_age_months: int = Field(ge=0)
    end_age_months: int = Field(ge=0)


class ProgressionRuleResponse(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    specific_product_id: uuid.UUID
    start_age_months: int
    end_age_months: int

    model_config = {"from_attributes": True}