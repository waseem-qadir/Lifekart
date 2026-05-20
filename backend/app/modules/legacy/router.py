import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.users.dependencies import get_current_user, require_role
from app.modules.users.models import User, UserRole
from app.modules.legacy.schemas import (
    LegacyNomineeCreate,
    LegacyNomineeUpdate,
    LegacyNomineeResponse,
    DeathVerificationRequest,
    LegacyActivationResponse,
)
from app.modules.legacy.service import LegacyService

router = APIRouter(prefix="/legacy")


@router.post("/nominees", response_model=LegacyNomineeResponse, status_code=status.HTTP_201_CREATED)
async def add_nominee(
    data: LegacyNomineeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = LegacyService(db)
    try:
        return await service.add_nominee(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/nominees", response_model=list[LegacyNomineeResponse])
async def list_nominees(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = LegacyService(db)
    return await service.get_nominees(current_user.id)


@router.patch("/nominees/{nominee_id}", response_model=LegacyNomineeResponse)
async def update_nominee(
    nominee_id: uuid.UUID,
    data: LegacyNomineeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = LegacyService(db)
    try:
        return await service.update_nominee(current_user.id, nominee_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/nominees/{nominee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_nominee(
    nominee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = LegacyService(db)
    try:
        await service.delete_nominee(current_user.id, nominee_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/verify-death", response_model=LegacyActivationResponse, status_code=status.HTTP_201_CREATED)
async def verify_death(
    data: DeathVerificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = LegacyService(db)
    try:
        return await service.verify_death_and_activate(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/activations/{activation_id}/approve", response_model=LegacyActivationResponse)
async def approve_activation(
    activation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN)),
):
    service = LegacyService(db)
    try:
        return await service.approve_activation(activation_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))