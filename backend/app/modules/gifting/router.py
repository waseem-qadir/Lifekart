import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.users.dependencies import get_current_user, require_role
from app.modules.users.models import User, UserRole
from app.modules.gifting.schemas import GiftOrderCreate, GiftOrderResponse
from app.modules.gifting.service import GiftingService

router = APIRouter(prefix="/gifting")


@router.post("/", response_model=GiftOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_gift_order(
    data: GiftOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = GiftingService(db)
    try:
        return await service.create_gift_order(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=list[GiftOrderResponse])
async def list_gift_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = GiftingService(db)
    return await service.get_my_gift_orders(current_user.id)


@router.get("/{gift_order_id}", response_model=GiftOrderResponse)
async def get_gift_order(
    gift_order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = GiftingService(db)
    try:
        gift = await service.get_gift_order(gift_order_id)
        await service._verify_ownership(current_user.id, gift)
        return gift
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{gift_order_id}/activate")
async def activate_gift_order(
    gift_order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = GiftingService(db)
    try:
        return await service.activate_gift_order(current_user.id, gift_order_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{gift_order_id}", response_model=GiftOrderResponse)
async def cancel_gift_order(
    gift_order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = GiftingService(db)
    try:
        return await service.cancel_gift_order(current_user.id, gift_order_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))