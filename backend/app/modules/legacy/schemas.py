import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LegacyNomineeCreate(BaseModel):
    nominee_name: str = Field(min_length=2, max_length=255)
    nominee_relationship: str = Field(
        min_length=2, max_length=30,
        pattern=r"^(spouse|child|parent|sibling|grandchild|niece|nephew|cousin|uncle|aunt|friend)$"
    )
    nominee_phone: Optional[str] = Field(None, max_length=20)
    nominee_email: Optional[str] = Field(None, max_length=255)
    nominee_aadhaar: Optional[str] = Field(None, max_length=12)
    is_primary: bool = False


class LegacyNomineeUpdate(BaseModel):
    nominee_name: Optional[str] = Field(None, min_length=2, max_length=255)
    nominee_relationship: Optional[str] = Field(
        None, min_length=2, max_length=30,
        pattern=r"^(spouse|child|parent|sibling|grandchild|niece|nephew|cousin|uncle|aunt|friend)$"
    )
    nominee_phone: Optional[str] = Field(None, max_length=20)
    nominee_email: Optional[str] = Field(None, max_length=255)
    nominee_aadhaar: Optional[str] = Field(None, max_length=12)
    is_primary: Optional[bool] = None


class LegacyNomineeResponse(BaseModel):
    id: uuid.UUID
    household_id: uuid.UUID
    nominee_name: str
    nominee_relationship: str
    nominee_phone: Optional[str]
    nominee_email: Optional[str]
    nominee_aadhaar: Optional[str]
    is_primary: bool
    is_verified: bool
    verification_status: str
    death_certificate_url: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class DeathVerificationRequest(BaseModel):
    nominee_id: uuid.UUID
    death_proof_type: str = Field(pattern=r"^(death_certificate|court_order|hospital_record|govt_notification)$")
    proof_document_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=1000)


class LegacyActivationResponse(BaseModel):
    id: uuid.UUID
    household_id: uuid.UUID
    original_user_id: uuid.UUID
    successor_nominee_id: uuid.UUID
    transfer_household_id: Optional[uuid.UUID]
    deceased_verified_at: Optional[datetime]
    activated_at: Optional[datetime]
    active_subscriptions_count: int
    transferred_count: int
    status: str
    activation_notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}