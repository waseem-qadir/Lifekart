from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.users.dependencies import require_role
from app.modules.users.models import User, UserRole
from app.modules.analytics.schemas import PlatformKpiResponse, LandingPageStatsResponse
from app.modules.analytics.service import AnalyticsService
from app.core.config import settings

router = APIRouter(prefix="/analytics")


@router.get("/public/config")
async def public_config():
    return {
        "max_lifetime_years": settings.MAX_LIFETIME_YEARS,
        "currency": "INR",
    }


@router.get("/kpi/savings", response_model=PlatformKpiResponse)
async def platform_kpi_savings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN)),
):
    service = AnalyticsService(db)
    result = await service.get_latest_platform_kpi("avg_monthly_household_savings")
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No KPI snapshot available yet")
    return result


@router.get("/public/landing-stats", response_model=LandingPageStatsResponse)
async def landing_page_stats(
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_landing_page_stats()