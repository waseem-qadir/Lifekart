import stripe

from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


async def create_stripe_payment_method(card_token: str) -> dict:
    return stripe.PaymentMethod.retrieve(card_token)


async def create_stripe_customer(email: str, name: str, payment_method_id: str) -> str:
    customer = stripe.Customer.create(
        email=email,
        name=name,
        payment_method=payment_method_id,
        invoice_settings={"default_payment_method": payment_method_id},
    )
    return customer.id


async def create_stripe_invoice(customer_id: str, amount: int, currency: str = "inr", description: str = "") -> dict:
    invoice = stripe.Invoice.create(
        customer=customer_id,
        currency=currency,
        description=description,
    )

    stripe.InvoiceItem.create(
        customer=customer_id,
        amount=amount,
        currency=currency,
        description=description,
        invoice=invoice.id,
    )

    finalized = stripe.Invoice.finalize_invoice(invoice.id)
    return finalized


async def pay_stripe_invoice(invoice_id: str) -> dict:
    return stripe.Invoice.pay(invoice_id)


async def attach_payment_method(customer_id: str, payment_method_id: str) -> dict:
    return stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)


async def detach_payment_method(payment_method_id: str) -> dict:
    return stripe.PaymentMethod.detach(payment_method_id)


async def set_default_payment_method(customer_id: str, payment_method_id: str) -> dict:
    return stripe.Customer.modify(
        customer_id,
        invoice_settings={"default_payment_method": payment_method_id},
    )