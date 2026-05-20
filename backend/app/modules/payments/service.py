import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payments.models import Invoice, PaymentMethod, PaymentTransaction, WebhookEvent
from app.modules.scheduling.models import DeliveryEvent
from app.modules.profiling.models import Household
from app.core.stripe_client import detach_payment_method


class PaymentsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_household(self, user_id: uuid.UUID) -> Household:
        result = await self.db.execute(
            select(Household).where(Household.user_id == user_id)
        )
        household = result.scalar_one_or_none()
        if not household:
            raise ValueError("Household not found")
        return household

    # ── Payment Methods ──

    async def add_payment_method(self, user_id: uuid.UUID, stripe_pm_id: str) -> PaymentMethod:
        import stripe as stripe_sdk
        household = await self.get_household(user_id)
        pm = stripe_sdk.PaymentMethod.retrieve(stripe_pm_id)

        result = await self.db.execute(
            select(PaymentMethod).where(
                PaymentMethod.household_id == household.id,
                PaymentMethod.is_default == True,
            )
        )
        has_default = result.scalar_one_or_none()

        method = PaymentMethod(
            household_id=household.id,
            stripe_payment_method_id=stripe_pm_id,
            type=pm.type or "card",
            last_four=pm.card.last4 if pm.card else None,
            is_default=not bool(has_default),
        )
        self.db.add(method)
        await self.db.flush()
        await self.db.refresh(method)
        return method

    async def get_payment_methods(self, user_id: uuid.UUID) -> list[PaymentMethod]:
        household = await self.get_household(user_id)
        result = await self.db.execute(
            select(PaymentMethod).where(PaymentMethod.household_id == household.id)
        )
        return list(result.scalars().all())

    async def remove_payment_method(self, user_id: uuid.UUID, method_id: uuid.UUID) -> None:
        household = await self.get_household(user_id)
        result = await self.db.execute(
            select(PaymentMethod).where(
                PaymentMethod.id == method_id,
                PaymentMethod.household_id == household.id,
            )
        )
        method = result.scalar_one_or_none()
        if not method:
            raise ValueError("Payment method not found")

        try:
            detach_payment_method(method.stripe_payment_method_id)
        except Exception:
            pass

        await self.db.delete(method)
        await self.db.flush()

    async def set_default(self, user_id: uuid.UUID, method_id: uuid.UUID) -> PaymentMethod:
        household = await self.get_household(user_id)

        result = await self.db.execute(
            select(PaymentMethod).where(
                PaymentMethod.id == method_id,
                PaymentMethod.household_id == household.id,
            )
        )
        method = result.scalar_one_or_none()
        if not method:
            raise ValueError("Payment method not found")

        result = await self.db.execute(
            select(PaymentMethod).where(
                PaymentMethod.household_id == household.id,
                PaymentMethod.is_default == True,
            )
        )
        for old in result.scalars().all():
            old.is_default = False

        method.is_default = True
        await self.db.flush()
        await self.db.refresh(method)
        return method

    # ── Invoices ──

    async def get_invoices(self, user_id: uuid.UUID) -> list[Invoice]:
        household = await self.get_household(user_id)
        result = await self.db.execute(
            select(Invoice)
            .where(Invoice.household_id == household.id)
            .order_by(Invoice.issued_at.desc())
            .limit(24)
        )
        return list(result.scalars().all())

    async def get_invoice(self, user_id: uuid.UUID, invoice_id: uuid.UUID) -> Invoice:
        household = await self.get_household(user_id)
        result = await self.db.execute(
            select(Invoice).where(
                Invoice.id == invoice_id,
                Invoice.household_id == household.id,
            )
        )
        invoice = result.scalar_one_or_none()
        if not invoice:
            raise ValueError("Invoice not found")
        return invoice

    async def generate_invoices_for_all(self) -> dict:
        today = date.today()
        first_of_month = today.replace(day=1)
        last_month_end = first_of_month - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)

        result = await self.db.execute(
            select(Household).where(Household.user_id.isnot(None))
        )
        households = list(result.scalars().all())

        generated = 0
        for household in households:
            deliveries = await self.db.execute(
                select(DeliveryEvent).where(
                    DeliveryEvent.household_id == household.id,
                    DeliveryEvent.scheduled_date >= last_month_start,
                    DeliveryEvent.scheduled_date <= last_month_end,
                )
            )
            delivery_list = list(deliveries.scalars().all())

            if not delivery_list:
                continue

            total = sum(
                d.unit_price_applied * d.quantity
                for d in delivery_list
                if d.unit_price_applied and d.quantity
            )

            invoice = Invoice(
                household_id=household.id,
                amount_total=Decimal(str(total)),
                amount_paid=Decimal("0"),
                currency="INR",
                status="draft",
                issued_at=datetime.now(timezone.utc),
                billing_period_start=last_month_start,
                billing_period_end=last_month_end,
            )
            self.db.add(invoice)
            generated += 1

        await self.db.commit()
        return {"invoices_generated": generated, "period": f"{last_month_start} → {last_month_end}"}

    # ── Webhook ──

    async def is_event_processed(self, stripe_event_id: str) -> bool:
        result = await self.db.execute(
            select(WebhookEvent).where(WebhookEvent.stripe_event_id == stripe_event_id)
        )
        return result.scalar_one_or_none() is not None

    async def record_webhook_event(self, stripe_event_id: str, event_type: str, payload: dict) -> WebhookEvent:
        event = WebhookEvent(
            stripe_event_id=stripe_event_id,
            event_type=event_type,
            payload=payload,
            is_processed=True,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def handle_payment_succeeded(self, stripe_invoice_id: str, amount: int, payment_intent_id: str) -> None:
        result = await self.db.execute(
            select(Invoice).where(Invoice.stripe_invoice_id == stripe_invoice_id)
        )
        invoice = result.scalar_one_or_none()
        if not invoice:
            return

        invoice.status = "paid"
        invoice.amount_paid = Decimal(str(amount / 100))
        invoice.paid_at = datetime.now(timezone.utc)

        txn = PaymentTransaction(
            invoice_id=invoice.id,
            stripe_payment_intent_id=payment_intent_id,
            amount=Decimal(str(amount / 100)),
            currency="INR",
            status="succeeded",
        )
        self.db.add(txn)

    async def handle_payment_failed(self, stripe_invoice_id: str) -> None:
        result = await self.db.execute(
            select(Invoice).where(Invoice.stripe_invoice_id == stripe_invoice_id)
        )
        invoice = result.scalar_one_or_none()
        if not invoice:
            return

        invoice.status = "uncollectible"