import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class DeliveryProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    image_url: Optional[str] = None
    unit_price_wholesale: Decimal
    
    model_config = {"from_attributes": True}


class DeliveryEventResponse(BaseModel):
    id: uuid.UUID
    subscription_id: uuid.UUID
    household_id: uuid.UUID
    product_id: uuid.UUID
    scheduled_date: date
    actual_delivery_date: Optional[datetime] = None
    status: str
    quantity: float
    unit_price_applied: Decimal
    tracking_number: Optional[str] = None
    delivery_address: dict
    notes: Optional[str] = None
    created_at: datetime
    product: Optional[DeliveryProductResponse] = None
    
    model_config = {"from_attributes": True}
