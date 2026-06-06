from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.users.dependencies import require_role
from app.modules.users.models import User, UserRole
from app.modules.scheduling.schemas import DeliveryEventResponse
from app.modules.scheduling.service import SchedulingService

router = APIRouter(prefix="/scheduling")

@router.get("/deliveries", response_model=list[DeliveryEventResponse])
async def get_my_deliveries(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER))
):
    service = SchedulingService(db)
    return await service.get_my_deliveries(current_user.id)
