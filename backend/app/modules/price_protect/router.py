import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.users.dependencies import get_current_user, require_role
from app.modules.users.models import User, UserRole
from app.modules.price_protect.schemas import (
    PriceHistoryResponse,
    PriceProtectionRuleCreate,
    PriceProtectionRuleResponse,
    SubstitutionEventCreate,
    SubstitutionEventResponse,
)
from app.modules.price_protect.service import PriceProtectionService

router = APIRouter(prefix="/price-protection")


@router.post("/rules", response_model=PriceProtectionRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    data: PriceProtectionRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN)),
):
    service = PriceProtectionService(db)
    return await service.create_rule(data)


@router.get("/rules", response_model=list[PriceProtectionRuleResponse])
async def list_rules(
    product_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PriceProtectionService(db)
    return await service.get_rules(product_id=product_id)


@router.get("/rules/{rule_id}", response_model=PriceProtectionRuleResponse)
async def get_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PriceProtectionService(db)
    try:
        return await service.get_rule(rule_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN)),
):
    service = PriceProtectionService(db)
    try:
        await service.delete_rule(rule_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/products/{product_id}/history", response_model=list[PriceHistoryResponse])
async def get_price_history(
    product_id: uuid.UUID,
    limit: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PriceProtectionService(db)
    return await service.get_price_history(product_id, limit=limit)


@router.get("/subscriptions/{subscription_id}/substitutions", response_model=list[SubstitutionEventResponse])
async def get_substitutions(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = PriceProtectionService(db)
    try:
        return await service.get_substitutions(current_user.id, subscription_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/subscriptions/{subscription_id}/substitute", response_model=SubstitutionEventResponse, status_code=status.HTTP_201_CREATED)
async def substitute_product(
    subscription_id: uuid.UUID,
    data: SubstitutionEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    if data.lifetime_subscription_id != subscription_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subscription ID mismatch")

    service = PriceProtectionService(db)
    try:
        return await service.add_substitution(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))