import uuid
from decimal import Decimal

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import (
    Manufacturer,
    Product,
    ProductCategory,
    ProductProgressionRule,
    ProductSubstitute,
)
from app.modules.catalog.schemas import (
    CategoryCreate,
    CategoryUpdate,
    ManufacturerCreate,
    ManufacturerUpdate,
    ProgressionRuleCreate,
    ProductCreate,
    ProductUpdate,
    SubstitutionCreate,
)


class CatalogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Categories ──

    async def create_category(self, data: CategoryCreate) -> ProductCategory:
        existing = await self.db.execute(
            select(ProductCategory).where(ProductCategory.slug == data.slug)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Category with slug '{data.slug}' already exists")

        category = ProductCategory(
            name=data.name,
            slug=data.slug,
            icon=data.icon,
            unit_type=data.unit_type,
            avg_lifetime_consumption_per_year=data.avg_lifetime_consumption_per_year,
        )
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def get_categories(self, skip: int = 0, limit: int = 100) -> list[ProductCategory]:
        result = await self.db.execute(
            select(ProductCategory).offset(skip).limit(limit).order_by(ProductCategory.name)
        )
        return list(result.scalars().all())

    async def get_category_by_id(self, category_id: uuid.UUID) -> ProductCategory:
        result = await self.db.execute(
            select(ProductCategory).where(ProductCategory.id == category_id)
        )
        category = result.scalar_one_or_none()
        if not category:
            raise ValueError("Category not found")
        return category

    async def get_category_by_slug(self, slug: str) -> ProductCategory:
        result = await self.db.execute(
            select(ProductCategory).where(ProductCategory.slug == slug)
        )
        category = result.scalar_one_or_none()
        if not category:
            raise ValueError("Category not found")
        return category

    async def update_category(self, category_id: uuid.UUID, data: CategoryUpdate) -> ProductCategory:
        category = await self.get_category_by_id(category_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def delete_category(self, category_id: uuid.UUID) -> None:
        category = await self.get_category_by_id(category_id)
        product_count = await self.db.execute(
            select(Product).where(Product.category_id == category_id)
        )
        if list(product_count.scalars().all()):
            raise ValueError("Cannot delete category with existing products")
        await self.db.delete(category)
        await self.db.flush()

    # ── Manufacturers ──

    async def create_manufacturer(self, user_id: uuid.UUID, data: ManufacturerCreate) -> Manufacturer:
        existing = await self.db.execute(
            select(Manufacturer).where(Manufacturer.user_id == user_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Manufacturer profile already exists for this user")

        if data.gstin:
            gstin_check = await self.db.execute(
                select(Manufacturer).where(Manufacturer.gstin == data.gstin)
            )
            if gstin_check.scalar_one_or_none():
                raise ValueError("A manufacturer with this GSTIN already exists")

        manufacturer = Manufacturer(
            user_id=user_id,
            company_name=data.company_name,
            gstin=data.gstin,
            address_line1=data.address_line1,
            address_line2=data.address_line2,
            city=data.city,
            state=data.state,
            pincode=data.pincode,
            contact_email=data.contact_email,
        )
        self.db.add(manufacturer)
        await self.db.flush()
        await self.db.refresh(manufacturer)
        return manufacturer

    async def get_manufacturers(self, skip: int = 0, limit: int = 50) -> list[Manufacturer]:
        result = await self.db.execute(
            select(Manufacturer).where(Manufacturer.is_verified == True).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_manufacturer_by_id(self, manufacturer_id: uuid.UUID) -> Manufacturer:
        result = await self.db.execute(
            select(Manufacturer).where(Manufacturer.id == manufacturer_id)
        )
        manufacturer = result.scalar_one_or_none()
        if not manufacturer:
            raise ValueError("Manufacturer not found")
        return manufacturer

    async def get_manufacturer_by_user(self, user_id: uuid.UUID) -> Manufacturer:
        result = await self.db.execute(
            select(Manufacturer).where(Manufacturer.user_id == user_id)
        )
        manufacturer = result.scalar_one_or_none()
        if not manufacturer:
            raise ValueError("Manufacturer profile not found for this user")
        return manufacturer

    async def update_manufacturer(self, manufacturer_id: uuid.UUID, data: ManufacturerUpdate) -> Manufacturer:
        manufacturer = await self.get_manufacturer_by_id(manufacturer_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(manufacturer, field, value)
        await self.db.flush()
        await self.db.refresh(manufacturer)
        return manufacturer

    async def verify_manufacturer(self, manufacturer_id: uuid.UUID) -> Manufacturer:
        manufacturer = await self.get_manufacturer_by_id(manufacturer_id)
        manufacturer.is_verified = True
        await self.db.flush()
        await self.db.refresh(manufacturer)
        return manufacturer

    # ── Products ──

    async def create_product(self, manufacturer_id: uuid.UUID, data: ProductCreate) -> Product:
        await self.get_category_by_id(data.category_id)

        existing = await self.db.execute(
            select(Product).where(Product.sku == data.sku)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Product with SKU '{data.sku}' already exists")

        product = Product(
            category_id=data.category_id,
            manufacturer_id=manufacturer_id,
            name=data.name,
            sku=data.sku,
            image_url=data.image_url,
            unit_size=data.unit_size,
            unit_price_wholesale=data.unit_price_wholesale,
            unit_price_retail=data.unit_price_retail,
            min_order_quantity=data.min_order_quantity,
            max_order_quantity=data.max_order_quantity,
        )
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product)
        await self._rebuild_substitutes_for_product(product.id, product.category_id, product.unit_price_wholesale)
        await self.db.commit()
        return product

    async def get_products(
        self,
        category_id: uuid.UUID | None = None,
        manufacturer_id: uuid.UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Product]:
        query = select(Product).where(Product.is_active == True)

        if category_id:
            query = query.where(Product.category_id == category_id)
        if manufacturer_id:
            query = query.where(Product.manufacturer_id == manufacturer_id)

        query = query.offset(skip).limit(limit).order_by(Product.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_product_by_id(self, product_id: uuid.UUID) -> Product:
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            raise ValueError("Product not found")
        return product

    async def get_product_by_sku(self, sku: str) -> Product:
        result = await self.db.execute(select(Product).where(Product.sku == sku))
        product = result.scalar_one_or_none()
        if not product:
            raise ValueError("Product not found")
        return product

    async def update_product(self, product_id: uuid.UUID, data: ProductUpdate) -> Product:
        product = await self.get_product_by_id(product_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def delete_product(self, product_id: uuid.UUID) -> None:
        product = await self.get_product_by_id(product_id)
        product.is_active = False
        await self.db.flush()

    # ── Substitutions ──

    async def add_substitute(self, data: SubstitutionCreate) -> ProductSubstitute:
        if data.product_id == data.substitute_product_id:
            raise ValueError("A product cannot be its own substitute")

        await self.get_product_by_id(data.product_id)
        await self.get_product_by_id(data.substitute_product_id)

        substitution = ProductSubstitute(
            product_id=data.product_id,
            substitute_product_id=data.substitute_product_id,
            priority_rank=data.priority_rank,
        )
        self.db.add(substitution)
        await self.db.flush()
        await self.db.refresh(substitution)
        return substitution

    async def get_substitutes(self, product_id: uuid.UUID) -> list[ProductSubstitute]:
        result = await self.db.execute(
            select(ProductSubstitute)
            .where(ProductSubstitute.product_id == product_id)
            .order_by(ProductSubstitute.priority_rank)
        )
        return list(result.scalars().all())

    async def remove_substitute(self, substitution_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(ProductSubstitute).where(ProductSubstitute.id == substitution_id)
        )
        sub = result.scalar_one_or_none()
        if not sub:
            raise ValueError("Substitution not found")
        await self.db.delete(sub)
        await self.db.flush()

    # ── Progression Rules ──

    async def add_progression_rule(self, data: ProgressionRuleCreate) -> ProductProgressionRule:
        await self.get_category_by_id(data.category_id)
        await self.get_product_by_id(data.specific_product_id)

        rule = ProductProgressionRule(
            category_id=data.category_id,
            specific_product_id=data.specific_product_id,
            start_age_months=data.start_age_months,
            end_age_months=data.end_age_months,
        )
        self.db.add(rule)
        await self.db.flush()
        await self.db.refresh(rule)
        return rule

    async def get_progression_rules(self, category_id: uuid.UUID) -> list[ProductProgressionRule]:
        result = await self.db.execute(
            select(ProductProgressionRule)
            .where(ProductProgressionRule.category_id == category_id)
            .order_by(ProductProgressionRule.start_age_months)
        )
        return list(result.scalars().all())

    async def remove_progression_rule(self, rule_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(ProductProgressionRule).where(ProductProgressionRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        if not rule:
            raise ValueError("Progression rule not found")
        await self.db.delete(rule)
        await self.db.flush()

    async def find_healthy_alternative(
        self, product_id: uuid.UUID, required_tags: list[str] | None = None, forbidden_tags: list[str] | None = None
    ) -> Product | None:
        from sqlalchemy import and_, or_, cast, String

        result = await self.db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            return None

        query = select(Product).where(
            Product.category_id == product.category_id,
            Product.is_active == True,
            Product.stock_quantity > 0,
            Product.id != product_id,
        )

        if required_tags:
            required_set = set(required_tags)
            query = query.where(
                or_(*[
                    Product.health_tags.cast(String).contains(tag)
                    for tag in required_set
                ])
            )

        if forbidden_tags:
            forbidden_set = set(forbidden_tags)
            query = query.where(
                and_(*[
                    ~Product.health_tags.cast(String).contains(tag)
                    for tag in forbidden_set
                ])
            )

        query = query.order_by(Product.unit_price_wholesale).limit(1)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _rebuild_substitutes_for_product(self, product_id: uuid.UUID, category_id: uuid.UUID, price: Decimal, max_alternatives: int = 3) -> None:
        from sqlalchemy import delete

        await self.db.execute(
            delete(ProductSubstitute).where(ProductSubstitute.product_id == product_id)
        )

        result = await self.db.execute(
            select(Product)
            .where(
                Product.category_id == category_id,
                Product.is_active == True,
                Product.stock_quantity > 0,
                Product.id != product_id,
            )
            .order_by(
                func.abs(Product.unit_price_wholesale - price)
            )
            .limit(max_alternatives)
        )
        alternatives = list(result.scalars().all())

        for rank, alt in enumerate(alternatives, start=1):
            sub = ProductSubstitute(
                product_id=product_id,
                substitute_product_id=alt.id,
                priority_rank=rank,
            )
            self.db.add(sub)

    async def rebuild_all_substitutes(self) -> dict:
        from sqlalchemy import delete

        await self.db.execute(delete(ProductSubstitute))

        result = await self.db.execute(select(Product).where(Product.is_active == True))
        active_products = list(result.scalars().all())

        total = 0
        for product in active_products:
            sub_result = await self.db.execute(
                select(Product)
                .where(
                    Product.category_id == product.category_id,
                    Product.is_active == True,
                    Product.stock_quantity > 0,
                    Product.id != product.id,
                )
                .order_by(
                    func.abs(Product.unit_price_wholesale - product.unit_price_wholesale)
                )
                .limit(3)
            )
            alternatives = list(sub_result.scalars().all())

            for rank, alt in enumerate(alternatives, start=1):
                sub = ProductSubstitute(
                    product_id=product.id,
                    substitute_product_id=alt.id,
                    priority_rank=rank,
                )
                self.db.add(sub)
                total += 1

        await self.db.commit()
        return {"products_processed": len(active_products), "substitutes_created": total}