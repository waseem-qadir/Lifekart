from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class UserSavingsResponse(BaseModel):
    monthly_savings: Decimal
    total_lifetime_savings: Decimal
    active_subscriptions: int
    deliveries_this_month: int
    period: str

    model_config = {"from_attributes": True}


class PlatformKpiResponse(BaseModel):
    metric_name: str
    metric_value: Decimal
    period_start: str
    period_end: str
    calculated_at: datetime

    model_config = {"from_attributes": True}


class LandingPageStatsResponse(BaseModel):
    advertised_avg_monthly_savings: Decimal
    total_active_households: int
    total_lifetime_contracts: int
    total_corporate_partners: int