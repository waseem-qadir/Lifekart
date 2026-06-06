import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payments.models import Invoice, PaymentMethod, PaymentTransaction, WebhookEvent
from app.modules.scheduling.models import DeliveryEvent
from app.modules.profiling.models import Household
from app.modules.users.models import User
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

    async def create_setup_intent(self, user_id: uuid.UUID) -> str:
        import stripe as stripe_sdk
        from app.core.config import settings
        stripe_sdk.api_key = settings.STRIPE_SECRET_KEY
        
        household = await self.get_household(user_id)
        
        if not household.stripe_customer_id:
            user_result = await self.db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one()
            
            customer = stripe_sdk.Customer.create(
                email=user.email,
                name=user.full_name,
                metadata={"household_id": str(household.id)}
            )
            household.stripe_customer_id = customer.id
            await self.db.flush()

        intent = stripe_sdk.SetupIntent.create(
            customer=household.stripe_customer_id,
            payment_method_types=['card'],
            usage='off_session',
            metadata={"household_id": str(household.id)}
        )
        return intent.client_secret

    async def add_payment_method(self, user_id: uuid.UUID, stripe_pm_id: str) -> PaymentMethod:
        import stripe as stripe_sdk
        from app.core.config import settings
        stripe_sdk.api_key = settings.STRIPE_SECRET_KEY
        
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
            brand=pm.card.brand if pm.card else None,
            last_four=pm.card.last4 if pm.card else None,
            exp_month=pm.card.exp_month if pm.card else None,
            exp_year=pm.card.exp_year if pm.card else None,
            is_default=not bool(has_default),
        )
        self.db.add(method)
        await self.db.flush()
        
        if method.is_default and household.stripe_customer_id:
            stripe_sdk.Customer.modify(
                household.stripe_customer_id,
                invoice_settings={"default_payment_method": stripe_pm_id}
            )
            
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
            await detach_payment_method(method.stripe_payment_method_id)
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
        
        import stripe as stripe_sdk
        from app.core.config import settings
        stripe_sdk.api_key = settings.STRIPE_SECRET_KEY
        if household.stripe_customer_id:
            stripe_sdk.Customer.modify(
                household.stripe_customer_id,
                invoice_settings={"default_payment_method": method.stripe_payment_method_id}
            )
            
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
        invoices = list(result.scalars().all())
        
        from app.modules.scheduling.models import DeliveryEvent
        from sqlalchemy.orm import joinedload
        
        # Attach line items
        for inv in invoices:
            deliv_res = await self.db.execute(
                select(DeliveryEvent)
                .options(joinedload(DeliveryEvent.product))
                .where(
                    DeliveryEvent.household_id == household.id,
                    DeliveryEvent.status.in_(["delivered", "processing", "completed"]),
                    DeliveryEvent.scheduled_date >= inv.billing_period_start,
                    DeliveryEvent.scheduled_date <= inv.billing_period_end,
                )
            )
            deliveries = deliv_res.scalars().all()
            line_items = []
            for d in deliveries:
                if d.unit_price_applied and d.quantity:
                    line_items.append({
                        "product_name": d.product.name if d.product else "LifeKart Product",
                        "quantity": float(d.quantity),
                        "unit_price": Decimal(str(d.unit_price_applied)),
                        "total": Decimal(str(d.unit_price_applied * Decimal(str(d.quantity))))
                    })
            # We can attach this dynamically to the object so pydantic picks it up
            setattr(inv, "line_items", line_items)
            
        return invoices

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
                
            # Prevent duplicates for the same billing period
            existing = await self.db.execute(
                select(Invoice).where(
                    Invoice.household_id == household.id,
                    Invoice.billing_period_start == last_month_start,
                    Invoice.billing_period_end == last_month_end
                )
            )
            if existing.scalar_one_or_none():
                continue

            total = sum(
                d.unit_price_applied * Decimal(str(d.quantity))
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

    async def handle_payment_succeeded(self, stripe_invoice_id: str, amount: int, payment_intent_id: str, hosted_invoice_url: str = None, invoice_pdf: str = None) -> None:
        result = await self.db.execute(
            select(Invoice).where(Invoice.stripe_invoice_id == stripe_invoice_id)
        )
        invoice = result.scalar_one_or_none()
        if not invoice:
            return

        # 1. Pull the actual, true total Stripe charged (converting paise to rupees)
        true_total = Decimal(str(amount / 100))
        
        # 2. Save it permanently into your database row so the serializer just reads it dumbly
        invoice.status = "paid"
        invoice.amount_total = true_total
        invoice.amount_paid = true_total
        invoice.paid_at = datetime.now(timezone.utc)
        
        if hosted_invoice_url:
            invoice.hosted_invoice_url = hosted_invoice_url
        if invoice_pdf:
            invoice.invoice_pdf = invoice_pdf
            
        await self.db.commit()

        txn = PaymentTransaction(
            invoice_id=invoice.id,
            stripe_payment_intent_id=payment_intent_id,
            amount=Decimal(str(amount / 100)),
            currency="INR",
            status="succeeded",
        )
        self.db.add(txn)

    async def handle_setup_intent_succeeded(self, setup_intent_id: str, payment_method_id: str, household_id_str: str) -> None:
        import stripe as stripe_sdk
        from app.core.config import settings
        stripe_sdk.api_key = settings.STRIPE_SECRET_KEY
        
        if not household_id_str:
            return
            
        household_id = uuid.UUID(household_id_str)
        pm = stripe_sdk.PaymentMethod.retrieve(payment_method_id)
        
        result = await self.db.execute(
            select(PaymentMethod).where(
                PaymentMethod.household_id == household_id,
                PaymentMethod.stripe_payment_method_id == payment_method_id
            )
        )
        if result.scalar_one_or_none():
            return
            
        result_def = await self.db.execute(
            select(PaymentMethod).where(
                PaymentMethod.household_id == household_id,
                PaymentMethod.is_default == True,
            )
        )
        has_default = result_def.scalar_one_or_none()
        
        method = PaymentMethod(
            household_id=household_id,
            stripe_payment_method_id=payment_method_id,
            type=pm.type or "card",
            brand=pm.card.brand if getattr(pm, 'card', None) else None,
            last_four=pm.card.last4 if getattr(pm, 'card', None) else None,
            exp_month=pm.card.exp_month if getattr(pm, 'card', None) else None,
            exp_year=pm.card.exp_year if getattr(pm, 'card', None) else None,
            is_default=not bool(has_default),
        )
        self.db.add(method)

    async def handle_payment_failed(self, stripe_invoice_id: str, hosted_invoice_url: str = None, invoice_pdf: str = None) -> None:
        result = await self.db.execute(
            select(Invoice).where(Invoice.stripe_invoice_id == stripe_invoice_id)
        )
        invoice = result.scalar_one_or_none()
        if not invoice:
            return

        invoice.status = "payment_failed"
        if hosted_invoice_url:
            invoice.hosted_invoice_url = hosted_invoice_url
        if invoice_pdf:
            invoice.invoice_pdf = invoice_pdf