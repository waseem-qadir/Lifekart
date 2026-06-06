import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.users.dependencies import get_current_user, require_role
from app.modules.users.models import User, UserRole
from app.modules.agreements.schemas import (
    AgreementCreate,
    AgreementItemCreate,
    AgreementItemResponse,
    AgreementItemUpdate,
    AgreementResponse,
    AgreementUpdate,
)
from app.modules.agreements.service import AgreementService

router = APIRouter(prefix="/agreements")


@router.post("/", response_model=AgreementResponse, status_code=status.HTTP_201_CREATED)
async def create_agreement(
    data: AgreementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = AgreementService(db)
    try:
        return await service.create_agreement(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=list[AgreementResponse])
async def list_agreements(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = AgreementService(db)
    return await service.get_my_agreements(current_user.id)


@router.get("/{agreement_id}", response_model=AgreementResponse)
async def get_agreement(
    agreement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = AgreementService(db)
    try:
        agreement = await service.get_agreement(agreement_id)
        await service._verify_ownership(current_user.id, agreement.household_id)
        return agreement
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{agreement_id}", response_model=AgreementResponse)
async def update_agreement(
    agreement_id: uuid.UUID,
    data: AgreementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = AgreementService(db)
    try:
        return await service.update_agreement(current_user.id, agreement_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{agreement_id}/items", response_model=AgreementItemResponse, status_code=status.HTTP_201_CREATED)
async def add_item(
    agreement_id: uuid.UUID,
    data: AgreementItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = AgreementService(db)
    try:
        return await service.add_item(current_user.id, agreement_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/items/{item_id}", response_model=AgreementItemResponse)
async def update_item(
    item_id: uuid.UUID,
    data: AgreementItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = AgreementService(db)
    try:
        return await service.update_item(current_user.id, item_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = AgreementService(db)
    try:
        await service.remove_item(current_user.id, item_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{agreement_id}/sign", response_model=AgreementResponse)
async def sign_agreement(
    agreement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = AgreementService(db)
    try:
        return await service.sign_agreement(current_user.id, agreement_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{agreement_id}", response_model=AgreementResponse)
async def cancel_agreement(
    agreement_id: uuid.UUID,
    reason: str = Query(""),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = AgreementService(db)
    try:
        return await service.cancel_agreement(current_user.id, agreement_id, reason)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))