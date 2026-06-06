from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.settings_model import SystemSetting, DEFAULTS

router = APIRouter(prefix="/config")

@router.get("/metadata")
async def get_metadata(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == "dietary_multipliers"))
    setting = result.scalar_one_or_none()
    
    diets = list(setting.value.keys()) if setting else list(DEFAULTS["dietary_multipliers"].keys())
    
    return {
        "diets": diets,
        "allergies": [
            "Peanuts", "Tree Nuts", "Dairy", "Eggs", "Soy", "Wheat", "Shellfish", "Gluten",
            "Latex", "Dust", "Pollen"
        ],
        "conditions": [
            "Diabetes Type 2", "High Blood Pressure", "Thyroid", "Asthma", "Lactose Intolerant",
            "Gluten Intolerant", "Arthritis", "PCOD/PCOS", "Low B12", "High Cholesterol"
        ],
        "relations": ["spouse", "child", "parent", "sibling", "grandparent"],
        "genders": ["male", "female", "other"],
        "blood_groups": ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    }
