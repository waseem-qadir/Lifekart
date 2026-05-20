import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CorporatePartnerCreate(BaseModel):
    company_name: str = Field(min_length=2, max_length=255)
    gstin: str | None = Field(None, min_length=10, max_length=20)
    industry: str | None = Field(None, max_length=100)
    employee_count: int | None = Field(None, ge=1)
    contact_email: str | None = Field(None, max_length=255)
    address_line1: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    pincode: str | None = Field(None, max_length=10)
    subsidy_percentage: Decimal | None = Field(None, ge=0, le=100)
    max_employee_benefit: Decimal | None = Field(None, ge=0)


class CorporatePartnerUpdate(BaseModel):
    company_name: str | None = Field(None, min_length=2, max_length=255)
    industry: str | None = Field(None, max_length=100)
    employee_count: int | None = Field(None, ge=1)
    contact_email: str | None = Field(None, max_length=255)
    address_line1: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    pincode: str | None = Field(None, max_length=10)
    subsidy_percentage: Decimal | None = Field(None, ge=0, le=100)
    max_employee_benefit: Decimal | None = Field(None, ge=0)


class CorporatePartnerResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    company_name: str
    gstin: str | None
    industry: str | None
    employee_count: int | None
    contact_email: str | None
    address_line1: str | None
    city: str | None
    state: str | None
    pincode: str | None
    partnership_status: str
    subsidy_percentage: Decimal | None
    max_employee_benefit: Decimal | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EmployeeEnrollCreate(BaseModel):
    household_id: uuid.UUID
    employee_id: str = Field(min_length=1, max_length=100)
    department: str | None = Field(None, max_length=100)
    designation: str | None = Field(None, max_length=100)


class EmployeeEnrollmentResponse(BaseModel):
    id: uuid.UUID
    corporate_id: uuid.UUID
    household_id: uuid.UUID
    employee_id: str
    department: str | None
    designation: str | None
    enrolled_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}