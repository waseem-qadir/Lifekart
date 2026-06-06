from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Any

from app.db.session import get_db
from app.core.settings_model import SystemSetting

router = APIRouter()

class SettingUpdate(BaseModel):
    value: dict[str, Any]

@router.patch("/settings/{key}")
async def update_setting(key: str, data: SettingUpdate, db: AsyncSession = Depends(get_db)):
    # In a real app, verify admin user here
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = result.scalar_one_or_none()
    
    if setting:
        setting.value = data.value
    else:
        setting = SystemSetting(key=key, value=data.value)
        db.add(setting)
        
    await db.commit()
    await db.refresh(setting)
    
    # Invalidate cache
    from app.core.settings_loader import _CACHE
    if key in _CACHE:
        del _CACHE[key]
        
    return {"status": "success", "setting": setting}
