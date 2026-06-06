import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.background import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.users.dependencies import get_current_user, require_role
from app.modules.users.models import User, UserRole
from app.modules.calculator.schemas import (
    GenerateRequest,
    GenerateResponse,
    SubscriptionResponse,
    SubscriptionUpdate,
    TaskStatusResponse,
)
from app.modules.calculator.service import SubscriptionService
from app.modules.profiling.service import ProfilingService
from app.tasks.calculator_tasks import generate_projections as celery_generate_projections
from app.core.redis import cache_set

router = APIRouter(prefix="/subscriptions")


# ═══════════════════════════ GENERATE PROJECTIONS ═══════════════════════════

@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_projections(
    data: GenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    profiling = ProfilingService(db)

    if data.household_id:
        household = await profiling.get_my_household(current_user.id)
        if str(data.household_id) != str(household.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Household does not belong to you",
            )
        household_id = str(data.household_id)
    else:
        household = await profiling.get_my_household(current_user.id)
        household_id = str(household.id)

    task = celery_generate_projections.apply_async(args=[household_id])
    await cache_set(f"task:{task.id}", {"status": "PENDING", "result": None}, ttl=86400)

    return GenerateResponse(task_id=task.id)


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    from celery.result import AsyncResult
    from app.tasks.celery_app import celery_app

    task_result = AsyncResult(task_id, app=celery_app)
    result_data = None
    if isinstance(task_result.result, dict):
        result_data = task_result.result

    return TaskStatusResponse(
        task_id=task_id,
        status=task_result.status,
        result=result_data,
    )


# ═══════════════════════════ SUBSCRIPTIONS ═══════════════════════════

@router.get("/", response_model=list[SubscriptionResponse])
async def list_subscriptions(
    status: str | None = Query(None, pattern=r"^(active|paused|completed|cancelled)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = SubscriptionService(db)
    return await service.get_my_subscriptions(current_user.id, status=status)


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = SubscriptionService(db)
    try:
        sub = await service.get_subscription(subscription_id)
        await service._verify_ownership(current_user.id, sub.household_id)
        return sub
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: uuid.UUID,
    data: SubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = SubscriptionService(db)
    try:
        return await service.update_subscription(current_user.id, subscription_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{subscription_id}/pause", response_model=SubscriptionResponse)
async def pause_subscription(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = SubscriptionService(db)
    try:
        return await service.pause_subscription(current_user.id, subscription_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{subscription_id}/resume", response_model=SubscriptionResponse)
async def resume_subscription(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = SubscriptionService(db)
    try:
        return await service.resume_subscription(current_user.id, subscription_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{subscription_id}/adjust-size", response_model=SubscriptionResponse)
async def adjust_size(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = SubscriptionService(db)
    try:
        return await service.adjust_size(current_user.id, subscription_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_subscription(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = SubscriptionService(db)
    try:
        await service.cancel_subscription(current_user.id, subscription_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))