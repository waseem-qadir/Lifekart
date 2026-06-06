import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timezone

from app.db.session import get_db
from app.modules.users.dependencies import get_current_user, require_role
from app.modules.users.models import User, UserRole
from app.modules.payroll.schemas import (
    BulkDeductionRequest,
    PayrollDeductionCreate,
    PayrollDeductionResponse,
)
from app.modules.payroll.service import PayrollService

router = APIRouter(prefix="/payroll")


@router.post("/deductions", response_model=PayrollDeductionResponse, status_code=status.HTTP_201_CREATED)
async def create_deduction(
    data: PayrollDeductionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CORPORATE_ADMIN)),
):
    service = PayrollService(db)
    try:
        return await service.create_deduction(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/deductions", response_model=list[PayrollDeductionResponse])
async def list_deductions(
    enrollment_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CORPORATE_ADMIN)),
):
    service = PayrollService(db)
    return await service.get_deductions(current_user.id, enrollment_id=enrollment_id)


@router.post("/deductions/{deduction_id}/process", response_model=PayrollDeductionResponse)
async def process_deduction(
    deduction_id: uuid.UUID,
    external_ref: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CORPORATE_ADMIN)),
):
    service = PayrollService(db)
    try:
        return await service.mark_processed(current_user.id, deduction_id, external_ref)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/deductions/bulk", response_model=list[PayrollDeductionResponse], status_code=status.HTTP_201_CREATED)
async def bulk_create_deductions(
    data: BulkDeductionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CORPORATE_ADMIN)),
):
    service = PayrollService(db)
    try:
        return await service.create_bulk_deductions(
            current_user.id, data.pay_period_start, data.pay_period_end, data.deduction_date
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))