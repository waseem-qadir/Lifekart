import json
from typing import Any, Optional

from sqlalchemy import Column, String, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


DEFAULTS: dict[str, dict[str, Any]] = {
    "community_discount_tiers": {
        "tiers": [
            {"threshold": 100, "discount_pct": 5.0},
            {"threshold": 500, "discount_pct": 10.0},
            {"threshold": 2000, "discount_pct": 15.0},
            {"threshold": 10000, "discount_pct": 20.0},
            {"threshold": 50000, "discount_pct": 25.0},
        ]
    },
    "dietary_multipliers": {
        "vegetarian": 1.0,
        "non_veg": 1.2,
        "vegan": 1.0,
        "jain": 0.9,
        "keto": 0.7,
        "diabetic": 0.6,
    },
    "lifestyle_tag_multipliers": {
        "gym": 1.5,
        "athlete": 1.8,
        "pregnant": 1.3,
        "elderly": 0.8,
        "infant": 1.0,
        "child": 0.5,
        "office-worker": 1.0,
    },
    "default_price_ceiling_pct": {"pct": 5.00},
    "organic_consumption_multiplier": {"rate": 1.1},
    "substitute_price_tolerance_pct": {"pct": 25.0},
    "substitute_max_alternatives": {"count": 3},
    "payroll_weeks_per_year": {"weeks": 52},
    "payroll_weeks_per_month": {"weeks": 4.33},
}


def get_default(key: str) -> dict[str, Any]:
    return DEFAULTS.get(key, {})