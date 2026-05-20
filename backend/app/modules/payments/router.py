import json
import uuid

import stripe
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import settings
from app.modules.users.dependencies import get_current_user, require_role
from app.modules.users.models import User, UserRole
from app.modules.payments.schemas import (
    InvoiceResponse,
    PaymentMethodCreate,
    PaymentMethodResponse,
)
from app.modules.payments.service import PaymentsService

router = APIRouter(prefix="/payments")


# ═══════════════════════════ PAYMENT METHODS ═══════════════════════════

@router.post("/methods", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
async def add_payment_method(
    data: PaymentMethodCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = PaymentsService(db)
    try:
        return await service.add_payment_method(current_user.id, data.stripe_payment_method_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/methods", response_model=list[PaymentMethodResponse])
async def list_payment_methods(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = PaymentsService(db)
    return await service.get_payment_methods(current_user.id)


@router.delete("/methods/{method_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_payment_method(
    method_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = PaymentsService(db)
    try:
        await service.remove_payment_method(current_user.id, method_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/methods/{method_id}/default", response_model=PaymentMethodResponse)
async def set_default_method(
    method_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = PaymentsService(db)
    try:
        return await service.set_default(current_user.id, method_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ═══════════════════════════ INVOICES ═══════════════════════════

@router.get("/invoices", response_model=list[InvoiceResponse])
async def list_invoices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = PaymentsService(db)
    return await service.get_invoices(current_user.id)


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    service = PaymentsService(db)
    try:
        return await service.get_invoice(current_user.id, invoice_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ═══════════════════════════ STRIPE WEBHOOK ═══════════════════════════

@router.post("/webhook/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing stripe-signature header")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")

    service = PaymentsService(db)

    if await service.is_event_processed(event.id):
        return {"status": "already_processed"}

    await service.record_webhook_event(event.id, event.type, event.data.to_dict() if hasattr(event, 'data') else {})

    data = event.data.object if hasattr(event, 'data') else None

    if event.type == "payment_intent.succeeded":
        if data and hasattr(data, 'invoice'):
            await service.handle_payment_succeeded(
                stripe_invoice_id=data.invoice,
                amount=data.amount_received,
                payment_intent_id=data.id,
            )
    elif event.type == "payment_intent.payment_failed":
        if data and hasattr(data, 'invoice') and data.invoice:
            await service.handle_payment_failed(stripe_invoice_id=data.invoice)

    await db.commit()
    return {"status": "processed", "event_type": event.type}