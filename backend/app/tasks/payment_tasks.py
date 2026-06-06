from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal, engine
from sqlalchemy import select
from app.modules.payments.models import Invoice, PaymentMethod
from app.modules.profiling.models import Household
import stripe
from app.core.config import settings
from decimal import Decimal

stripe.api_key = settings.STRIPE_SECRET_KEY

@celery_app.task(name="app.tasks.payment_tasks.process_due_payments")
def process_due_payments():
    import asyncio

    async def _run():
        await engine.dispose()
        try:
            async with AsyncSessionLocal() as db:
                # Find draft invoices
                result = await db.execute(
                    select(Invoice).where(Invoice.status == "draft")
                )
                invoices = result.scalars().all()
                processed = 0
                errors = 0

                for invoice in invoices:
                    try:
                        # Get Household
                        household_result = await db.execute(
                            select(Household).where(Household.id == invoice.household_id)
                        )
                        household = household_result.scalar_one_or_none()
                        
                        if not household or not household.stripe_customer_id:
                            continue

                        # 1. Iterate through the actual deliveries that need to be billed
                        from sqlalchemy.orm import joinedload
                        from app.modules.scheduling.models import DeliveryEvent
                        
                        deliveries_result = await db.execute(
                            select(DeliveryEvent)
                            .options(joinedload(DeliveryEvent.product))
                            .where(
                                DeliveryEvent.household_id == household.id,
                                DeliveryEvent.scheduled_date >= invoice.billing_period_start,
                                DeliveryEvent.scheduled_date <= invoice.billing_period_end,
                            )
                        )
                        delivery_list = list(deliveries_result.scalars().all())

                        # Clear any existing pending invoice items that might have old/ghost prices
                        pending_items = stripe.InvoiceItem.list(customer=household.stripe_customer_id, pending=True)
                        for item in pending_items.auto_paging_iter():
                            try:
                                stripe.InvoiceItem.delete(item.id)
                            except Exception:
                                pass

                        for delivery in delivery_list:
                            # Developer 40 must add an InvoiceItem for each physical product line first!
                            prod_name = delivery.product.name if delivery.product else "LifeKart Product"
                            stripe.InvoiceItem.create(
                                customer=household.stripe_customer_id,
                                unit_amount_decimal=str(int(float(delivery.product.unit_price_wholesale if delivery.product else delivery.unit_price_applied) * 100)), # Stripe expects values in Paise (cents)
                                quantity_decimal=str(delivery.quantity),
                                currency="inr",
                                description=f"{prod_name} - Standard Delivery",
                            )

                        # Create Stripe Invoice
                        stripe_invoice = stripe.Invoice.create(
                            customer=household.stripe_customer_id,
                            auto_advance=True, # Auto finalize
                            pending_invoice_items_behavior="include",
                            description=f"LifeKart Monthly Invoice — Billing Period: {invoice.billing_period_start.strftime('%-d/%-m/%Y')} to {invoice.billing_period_end.strftime('%-d/%-m/%Y')}",
                            metadata={"internal_invoice_id": str(invoice.id)}
                        )

                        # Update internal DB with stripe_invoice_id
                        invoice.stripe_invoice_id = stripe_invoice.id
                        
                        # Try to pay immediately
                        try:
                            stripe_invoice = stripe.Invoice.finalize_invoice(stripe_invoice.id)
                            paid_invoice = stripe.Invoice.pay(stripe_invoice.id, off_session=True)
                            
                            invoice.status = "paid"
                            
                            # Lock in the true total from Stripe
                            if hasattr(paid_invoice, "amount_paid") and paid_invoice.amount_paid is not None:
                                true_total = Decimal(str(paid_invoice.amount_paid / 100))
                                invoice.amount_total = true_total
                                invoice.amount_paid = true_total
                                
                            if hasattr(paid_invoice, "invoice_pdf") and paid_invoice.invoice_pdf:
                                invoice.invoice_pdf = paid_invoice.invoice_pdf
                            if hasattr(paid_invoice, "hosted_invoice_url") and paid_invoice.hosted_invoice_url:
                                invoice.hosted_invoice_url = paid_invoice.hosted_invoice_url
                                
                        except stripe.error.CardError as e:
                            # Payment failed, but invoice exists
                            invoice.status = "payment_failed"
                            errors += 1
                            continue

                        processed += 1
                    except Exception as e:
                        print(f"Error processing invoice {invoice.id}: {e}")
                        errors += 1

                await db.commit()
                return {"processed": processed, "errors": errors}
        finally:
            await engine.dispose()

    return asyncio.run(_run())
