import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.users.dependencies import get_current_user, require_role
from app.modules.users.models import User, UserRole
from app.modules.corporate.schemas import (
    CorporatePartnerCreate,
    CorporatePartnerResponse,
    CorporatePartnerUpdate,
    EmployeeEnrollCreate,
    EmployeeEnrollmentResponse,
)
from app.modules.corporate.service import CorporateService

router = APIRouter(prefix="/corporate")


@router.get("/partners", response_model=list[CorporatePartnerResponse])
async def list_all_partners(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN)),
):
    service = CorporateService(db)
    return await service.list_all_partners()


@router.post("/partners/{partner_id}/approve", response_model=CorporatePartnerResponse)
async def approve_partner(
    partner_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPERADMIN)),
):
    service = CorporateService(db)
    try:
        return await service.approve_partner(partner_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/partners", response_model=CorporatePartnerResponse, status_code=status.HTTP_201_CREATED)
async def create_partner(
    data: CorporatePartnerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CORPORATE_ADMIN)),
):
    service = CorporateService(db)
    try:
        return await service.create_partner(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/partners/me", response_model=CorporatePartnerResponse)
async def get_my_partner(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CORPORATE_ADMIN)),
):
    service = CorporateService(db)
    try:
        return await service.get_my_partner(current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/partners/me", response_model=CorporatePartnerResponse)
async def update_partner(
    data: CorporatePartnerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CORPORATE_ADMIN)),
):
    service = CorporateService(db)
    try:
        return await service.update_partner(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/partners/me/employees", response_model=EmployeeEnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def enroll_employee(
    data: EmployeeEnrollCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CORPORATE_ADMIN)),
):
    service = CorporateService(db)
    try:
        return await service.enroll_employee(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/partners/me/employees", response_model=list[EmployeeEnrollmentResponse])
async def list_employees(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CORPORATE_ADMIN)),
):
    service = CorporateService(db)
    return await service.get_employees(current_user.id)


@router.delete("/employees/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_employee(
    enrollment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CORPORATE_ADMIN)),
):
    service = CorporateService(db)
    try:
        await service.remove_employee(current_user.id, enrollment_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))