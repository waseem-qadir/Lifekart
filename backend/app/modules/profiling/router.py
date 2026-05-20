import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.users.dependencies import get_current_user, require_role
from app.modules.users.models import User, UserRole
from app.modules.profiling.schemas import (
    HouseholdCreate,
    HouseholdResponse,
    HouseholdUpdate,
    MemberCreate,
    MemberResponse,
    MemberUpdate,
)
from app.modules.profiling.service import ProfilingService

router = APIRouter(prefix="/profiling")


# ═══════════════════════════ HOUSEHOLD ═══════════════════════════

@router.post("/households", response_model=HouseholdResponse, status_code=status.HTTP_201_CREATED)
async def create_household(
    data: HouseholdCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = ProfilingService(db)
    try:
        return await service.create_household(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/households/me", response_model=HouseholdResponse)
async def get_my_household(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = ProfilingService(db)
    try:
        return await service.get_my_household(current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/households/me", response_model=HouseholdResponse)
async def update_my_household(
    data: HouseholdUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = ProfilingService(db)
    try:
        return await service.update_household(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ═══════════════════════════ MEMBERS ═══════════════════════════

@router.get("/households/me/members", response_model=list[MemberResponse])
async def list_members(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = ProfilingService(db)
    return await service.get_household_members(current_user.id)


@router.post("/households/me/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    data: MemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = ProfilingService(db)
    try:
        return await service.add_member(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/members/{member_id}", response_model=MemberResponse)
async def get_member(
    member_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = ProfilingService(db)
    member = await service.get_member(member_id)
    household = await service.get_my_household(current_user.id)
    if member.household_id != household.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your household member")
    return member


@router.patch("/members/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: uuid.UUID,
    data: MemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = ProfilingService(db)
    try:
        return await service.update_member(current_user.id, member_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_member(
    member_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = ProfilingService(db)
    try:
        await service.deactivate_member(current_user.id, member_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))