import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.modules.agreements.models import AgreementItem, WholesaleAgreement
from app.modules.agreements.schemas import (
    AgreementCreate,
    AgreementItemCreate,
    AgreementItemUpdate,
    AgreementUpdate,
)
from app.modules.catalog.models import Manufacturer, Product
from app.modules.calculator.models import LifetimeSubscription
from app.modules.profiling.models import Household


from decimal import Decimal


class AgreementService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_agreement(self, user_id: uuid.UUID, data: AgreementCreate) -> WholesaleAgreement:
        result = await self.db.execute(
            select(Household).where(Household.user_id == user_id)
        )
        household = result.scalar_one_or_none()
        if not household:
            raise ValueError("Create your household profile first")

        result = await self.db.execute(
            select(Manufacturer).where(
                Manufacturer.id == data.manufacturer_id,
                Manufacturer.is_verified == True,
            )
        )
        manufacturer = result.scalar_one_or_none()
        if not manufacturer:
            raise ValueError("Manufacturer not found or not verified")

        duration_days = (data.end_date - data.start_date).days
        years = max(duration_days / 365.25, 1)

        total_value = sum(
            item.locked_unit_price * Decimal(str(item.committed_monthly_qty)) * Decimal("12") * Decimal(str(years))
            for item in data.items
        )

        agreement = WholesaleAgreement(
            household_id=household.id,
            manufacturer_id=data.manufacturer_id,
            status="draft",
            start_date=data.start_date,
            end_date=data.end_date,
            price_ceiling_agreed=data.price_ceiling_agreed,
            total_contract_value=total_value,
        )
        self.db.add(agreement)
        await self.db.flush()

        for item_data in data.items:
            item = AgreementItem(
                agreement_id=agreement.id,
                product_id=item_data.product_id,
                locked_unit_price=item_data.locked_unit_price,
                committed_monthly_qty=item_data.committed_monthly_qty,
                frequency_days=item_data.frequency_days,
                total_item_value=Decimal(str(item_data.locked_unit_price)) * Decimal(str(item_data.committed_monthly_qty)) * Decimal("12") * Decimal(str(years)),
            )
            self.db.add(item)

        await self.db.commit()
        return await self._get_with_items(agreement.id)

    async def get_my_agreements(self, user_id: uuid.UUID) -> list[WholesaleAgreement]:
        result = await self.db.execute(
            select(Household).where(Household.user_id == user_id)
        )
        household = result.scalar_one_or_none()
        if not household:
            return []

        result = await self.db.execute(
            select(WholesaleAgreement)
            .where(WholesaleAgreement.household_id == household.id)
            .options(selectinload(WholesaleAgreement.items).joinedload(AgreementItem.product))
            .order_by(WholesaleAgreement.created_at.desc())
        )
        return list(result.unique().scalars().all())

    async def get_agreement(self, agreement_id: uuid.UUID) -> WholesaleAgreement:
        result = await self.db.execute(
            select(WholesaleAgreement)
            .where(WholesaleAgreement.id == agreement_id)
            .options(selectinload(WholesaleAgreement.items).joinedload(AgreementItem.product))
        )
        agreement = result.scalar_one_or_none()
        if not agreement:
            raise ValueError("Agreement not found")
        return agreement

    async def update_agreement(
        self, user_id: uuid.UUID, agreement_id: uuid.UUID, data: AgreementUpdate
    ) -> WholesaleAgreement:
        agreement = await self.get_agreement(agreement_id)
        await self._verify_ownership(user_id, agreement.household_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(agreement, field, value)
        await self.db.commit()
        return await self._get_with_items(agreement.id)

    async def add_item(
        self, user_id: uuid.UUID, agreement_id: uuid.UUID, data: AgreementItemCreate
    ) -> AgreementItem:
        agreement = await self.get_agreement(agreement_id)
        await self._verify_ownership(user_id, agreement.household_id)

        if agreement.status != "draft":
            raise ValueError("Can only add items to draft agreements")

        duration_days = (agreement.end_date - agreement.start_date).days
        years = max(duration_days / 365.25, 1)

        item = AgreementItem(
            agreement_id=agreement_id,
            product_id=data.product_id,
            locked_unit_price=data.locked_unit_price,
            committed_monthly_qty=data.committed_monthly_qty,
            frequency_days=data.frequency_days,
            total_item_value=Decimal(str(data.locked_unit_price)) * Decimal(str(data.committed_monthly_qty)) * Decimal("12") * Decimal(str(years)),
        )
        self.db.add(item)
        await self.db.commit()
        
        # Re-fetch the item with its product relationship loaded to prevent MissingGreenlet errors
        result = await self.db.execute(
            select(AgreementItem)
            .where(AgreementItem.id == item.id)
            .options(joinedload(AgreementItem.product))
        )
        return result.scalar_one()

    async def update_item(
        self, user_id: uuid.UUID, item_id: uuid.UUID, data: AgreementItemUpdate
    ) -> AgreementItem:
        result = await self.db.execute(select(AgreementItem).where(AgreementItem.id == item_id))
        item = result.scalar_one_or_none()
        if not item:
            raise ValueError("Item not found")

        agreement = await self.get_agreement(item.agreement_id)
        await self._verify_ownership(user_id, agreement.household_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def remove_item(self, user_id: uuid.UUID, item_id: uuid.UUID) -> None:
        result = await self.db.execute(select(AgreementItem).where(AgreementItem.id == item_id))
        item = result.scalar_one_or_none()
        if not item:
            raise ValueError("Item not found")

        agreement = await self.get_agreement(item.agreement_id)
        await self._verify_ownership(user_id, agreement.household_id)

        if agreement.status != "draft":
            raise ValueError("Can only remove items from draft agreements")

        await self.db.delete(item)
        await self.db.commit()

    async def sign_agreement(self, user_id: uuid.UUID, agreement_id: uuid.UUID) -> WholesaleAgreement:
        agreement = await self.get_agreement(agreement_id)
        await self._verify_ownership(user_id, agreement.household_id)

        if agreement.status != "draft":
            raise ValueError(f"Cannot sign agreement with status '{agreement.status}'")
        if not agreement.items:
            raise ValueError("Agreement must have at least one item to sign")

        agreement.status = "active"
        agreement.signed_at = datetime.now(timezone.utc)

        product_ids = [item.product_id for item in agreement.items]
        existing_subs_result = await self.db.execute(
            select(LifetimeSubscription).where(
                LifetimeSubscription.household_id == agreement.household_id,
                LifetimeSubscription.product_id.in_(product_ids),
                LifetimeSubscription.source == "direct",
                LifetimeSubscription.source_id == agreement.id,
            )
        )
        existing_product_ids = {sub.product_id for sub in existing_subs_result.scalars().all()}

        for item in agreement.items:
            if item.product_id in existing_product_ids:
                continue

            sub = LifetimeSubscription(
                household_id=agreement.household_id,
                member_id=None,
                product_id=item.product_id,
                quantity_per_delivery=float(item.committed_monthly_qty) / (30 / item.frequency_days),
                frequency_days=item.frequency_days,
                start_date=agreement.start_date,
                end_date=agreement.end_date,
                next_delivery_date=agreement.start_date,
                status="active",
                source="direct",
                source_id=agreement.id,
                locked_unit_price=item.locked_unit_price,
                price_ceiling_pct=Decimal(str(agreement.price_ceiling_agreed)) if agreement.price_ceiling_agreed else Decimal("0"),
            )
            self.db.add(sub)

        duration_days = (agreement.end_date - agreement.start_date).days
        years = max(duration_days / 365.25, 1)
        
        agreement.total_contract_value = sum(
            (Decimal(str(item.locked_unit_price or 0))) * Decimal(str(item.committed_monthly_qty)) * Decimal("12") * Decimal(str(years))
            for item in agreement.items
        )

        await self.db.commit()
        return await self._get_with_items(agreement.id)

    async def cancel_agreement(self, user_id: uuid.UUID, agreement_id: uuid.UUID, reason: str = "") -> WholesaleAgreement:
        agreement = await self.get_agreement(agreement_id)
        await self._verify_ownership(user_id, agreement.household_id)

        if agreement.status not in ("draft", "active"):
            raise ValueError(f"Cannot cancel agreement with status '{agreement.status}'")

        agreement.status = "cancelled"
        agreement.cancelled_at = datetime.now(timezone.utc)
        agreement.cancellation_reason = reason or None

        result = await self.db.execute(
            select(LifetimeSubscription).where(
                LifetimeSubscription.source_id == agreement_id,
                LifetimeSubscription.source == "direct",
            )
        )
        for sub in result.scalars().all():
            sub.status = "cancelled"

        await self.db.commit()
        return await self._get_with_items(agreement.id)

    async def _get_with_items(self, agreement_id: uuid.UUID) -> WholesaleAgreement:
        result = await self.db.execute(
            select(WholesaleAgreement)
            .where(WholesaleAgreement.id == agreement_id)
            .options(selectinload(WholesaleAgreement.items).joinedload(AgreementItem.product))
        )
        return result.scalar_one()

    async def _verify_ownership(self, user_id: uuid.UUID, household_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(Household).where(
                Household.id == household_id,
                Household.user_id == user_id,
            )
        )
        if not result.scalar_one_or_none():
            raise ValueError("Agreement does not belong to you")