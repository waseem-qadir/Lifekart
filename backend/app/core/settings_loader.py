from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings_model import SystemSetting, get_default


async def load_settings(db: AsyncSession, keys: list[str]) -> dict[str, dict[str, Any]]:
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key.in_(keys))
    )
    db_settings = {s.key: s.value for s in result.scalars().all()}

    resolved: dict[str, dict[str, Any]] = {}
    for key in keys:
        resolved[key] = db_settings.get(key, get_default(key))

    return resolved


async def load_setting(db: AsyncSession, key: str) -> dict[str, Any]:
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == key)
    )
    setting = result.scalar_one_or_none()
    if setting:
        return setting.value
    return get_default(key)