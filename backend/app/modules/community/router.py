import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.users.dependencies import get_current_user, require_role
from app.modules.users.models import User, UserRole
from app.modules.community.schemas import (
    CommunityGroupCreate,
    CommunityGroupResponse,
    CommunityMembershipResponse,
)
from app.modules.community.service import CommunityService

router = APIRouter(prefix="/community")


@router.post("/groups", response_model=CommunityGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: CommunityGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = CommunityService(db)
    try:
        return await service.create_group(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/groups", response_model=list[CommunityGroupResponse])
async def list_groups(
    pincode: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CommunityService(db)
    return await service.get_groups(pincode=pincode)


@router.post("/groups/{group_id}/join", response_model=CommunityMembershipResponse, status_code=status.HTTP_201_CREATED)
async def join_group(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = CommunityService(db)
    try:
        return await service.join_group(current_user.id, group_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))