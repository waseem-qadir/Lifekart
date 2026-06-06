from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings_model import SystemSetting, get_default


import time

_CACHE = {}
_CACHE_TTL = 300  # 5 minutes in seconds

async def load_settings(db: AsyncSession, keys: list[str]) -> dict[str, dict[str, Any]]:
    now = time.time()
    
    cached_result = {}
    missing_keys = []
    
    for key in keys:
        if key in _CACHE and now - _CACHE[key]["timestamp"] < _CACHE_TTL:
            cached_result[key] = _CACHE[key]["value"]
        else:
            missing_keys.append(key)
            
    if not missing_keys:
        return cached_result
        
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key.in_(missing_keys))
    )
    db_settings = {s.key: s.value for s in result.scalars().all()}

    for key in missing_keys:
        value = db_settings.get(key, get_default(key))
        _CACHE[key] = {"value": value, "timestamp": now}
        cached_result[key] = value

    return cached_result

async def load_setting(db: AsyncSession, key: str) -> dict[str, Any]:
    res = await load_settings(db, [key])
    return res[key]