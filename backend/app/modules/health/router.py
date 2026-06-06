import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.users.dependencies import get_current_user, require_role
from app.modules.users.models import User, UserRole
from app.modules.health.schemas import (
    HealthProfileResponse,
    HealthProfileUpdate,
    HealthTransitionCreate,
    HealthTransitionResponse,
)
from app.modules.health.service import HealthService

router = APIRouter(prefix="/health")


@router.get("/profiles/{member_id}", response_model=HealthProfileResponse)
async def get_profile(
    member_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = HealthService(db)
    try:
        return await service.get_profile(member_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/profiles/{member_id}", response_model=HealthProfileResponse)
async def update_profile(
    member_id: uuid.UUID,
    data: HealthProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = HealthService(db)
    try:
        return await service.update_profile(member_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/transitions", response_model=HealthTransitionResponse, status_code=status.HTTP_201_CREATED)
async def create_transition(
    data: HealthTransitionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = HealthService(db)
    try:
        return await service.create_transition(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/transitions/{member_id}", response_model=list[HealthTransitionResponse])
async def get_transitions(
    member_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = HealthService(db)
    return await service.get_transitions(member_id)