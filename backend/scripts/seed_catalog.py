import asyncio
import sys
import os
import random  # <--- Added for random stock generation
from decimal import Decimal
from sqlalchemy import select

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app.main  # ensure all models are imported and registered

from app.db.session import AsyncSessionLocal
from app.modules.catalog.models import (
    Manufacturer,
    Product,
    ProductCategory,
    ProductProgressionRule,
)
from app.modules.users.models import User, UserRole
from app.core.security import hash_password

CATEGORIES = [
    ("Rice", "rice", "kg", 60, None),
    ("Wheat Flour", "wheat-flour", "kg", 120, None),
    ("Toothpaste", "toothpaste", "piece", 12, None),
    ("Toothbrush", "toothbrush", "piece", 4, None),
    ("Bathing Soap", "bathing-soap", "piece", 24, None),
    ("Shampoo", "shampoo", "piece", 12, None),
    ("Laundry Detergent", "laundry-detergent", "kg", 24, None),
    ("Dishwashing Liquid", "dishwashing-liquid", "piece", 12, None),
    ("Cooking Oil", "cooking-oil", "liter", 36, None),
    ("Sugar", "sugar", "kg", 24, None),
    ("Salt", "salt", "kg", 12, None),
    ("Tea", "tea", "kg", 6, None),
    ("Coffee", "coffee", "kg", 4, None),
    ("Milk", "milk", "liter", 365, None),
    ("Curd/Yogurt", "curd-yogurt", "liter", 180, None),
    ("Butter", "butter", "kg", 12, None),
    ("Cheese", "cheese", "kg", 6, None),
    ("Eggs", "eggs", "piece", 360, None),
    ("Chicken", "chicken", "kg", 24, None),
    ("Fish", "fish", "kg", 12, None),
    ("Lentils (Dal)", "lentils-dal", "kg", 36, None),
    ("Chickpeas", "chickpeas", "kg", 12, None),
    ("Kidney Beans", "kidney-beans", "kg", 12, None),
    ("Onions", "onions", "kg", 60, None),
    ("Potatoes", "potatoes", "kg", 72, None),
    ("Tomatoes", "tomatoes", "kg", 48, None),
    ("Garlic", "garlic", "kg", 6, None),
    ("Ginger", "ginger", "kg", 6, None),
    ("Green Chillies", "green-chillies", "kg", 6, None),
    ("Coriander Leaves", "coriander-leaves", "pack", 24, None),
    ("Bananas", "bananas", "kg", 48, None),
    ("Apples", "apples", "kg", 24, None),
    ("Oranges", "oranges", "kg", 24, None),
    ("Bread", "bread", "pack", 180, None),
    ("Breakfast Cereal", "breakfast-cereal", "kg", 12, None),
    ("Biscuits", "biscuits", "pack", 48, None),
    ("Jam", "jam", "kg", 6, None),
    ("Peanut Butter", "peanut-butter", "kg", 4, None),
    ("Spices - Turmeric", "spices-turmeric", "kg", 2, None),
    ("Spices - Red Chilli", "spices-red-chilli", "kg", 2, None),
    ("Spices - Cumin", "spices-cumin", "kg", 2, None),
    ("Spices - Coriander", "spices-coriander", "kg", 2, None),
    ("Spices - Garam Masala", "spices-garam-masala", "kg", 2, None),
    ("Tissue Paper", "tissue-paper", "pack", 48, None),
    ("Aluminum Foil", "aluminum-foil", "pack", 6, None),
    ("Plastic Wrap", "plastic-wrap", "pack", 6, None),
    ("Garbage Bags", "garbage-bags", "pack", 24, None),
    ("School Uniform", "school-uniform", "piece", 3, 18),
    ("School Shoes", "school-shoes", "pair", 2, 18),
    ("School Bag", "school-bag", "piece", 1, 18),
    ("Notebooks", "notebooks", "piece", 24, 22),
    ("Pens & Pencils", "pens-pencils", "pack", 12, 22),
    ("Diapers", "diapers", "pack", 360, 4),
    ("Baby Wipes", "baby-wipes", "pack", 120, 4),
    ("Baby Food", "baby-food", "kg", 24, 4),
    ("Pet Food - Dog", "pet-food-dog", "kg", 48, None),
    ("Pet Food - Cat", "pet-food-cat", "kg", 36, None),
    ("Mineral Water", "mineral-water", "liter", 180, None),
    ("Soft Drinks", "soft-drinks", "liter", 24, None),
    ("Juice", "juice", "liter", 24, None),
    ("Hand Wash", "hand-wash", "piece", 12, None),
    ("Floor Cleaner", "floor-cleaner", "liter", 6, None),
    ("Surface Disinfectant", "surface-disinfectant", "liter", 6, None),
    ("Toilet Cleaner", "toilet-cleaner", "liter", 6, None),
    ("Sanitary Pads", "sanitary-pads", "pack", 72, None),
    ("Razors", "razors", "piece", 52, None),
    ("Shaving Cream", "shaving-cream", "piece", 6, None),
    ("Deodorant", "deodorant", "piece", 12, None),
    ("Sunscreen", "sunscreen", "piece", 6, None),
    ("Moisturizer", "moisturizer", "piece", 6, None),
    ("Lip Balm", "lip-balm", "piece", 6, None),
    ("Hair Oil", "hair-oil", "piece", 6, None),
    ("Cotton Swabs", "cotton-swabs", "pack", 12, None),
    ("First-Aid Bandages", "first-aid-bandages", "pack", 6, None),
    ("Multivitamin Tablets", "multivitamin-tablets", "pack", 12, None),
    ("Protein Powder", "protein-powder", "kg", 6, None),
    ("Pasta", "pasta", "kg", 12, None),
    ("Noodles", "noodles", "kg", 12, None),
]

PROGRESSION_RULES = {
    "school-uniform": [
        ("UNIFORM-SIZE-S", 48, 107),
        ("UNIFORM-SIZE-M", 108, 179),
        ("UNIFORM-SIZE-L", 180, 215),
        ("UNIFORM-SIZE-XL", 216, 300),
    ],
    "school-shoes": [
        ("SHOE-UK10", 36, 59),
        ("SHOE-UK12", 60, 83),
        ("SHOE-UK1", 84, 107),
        ("SHOE-UK3", 108, 131),
        ("SHOE-UK5", 132, 155),
        ("SHOE-UK7", 156, 179),
        ("SHOE-UK9", 180, 300),
    ],
    "diapers": [
        ("DIAPER-NB", 0, 3),
        ("DIAPER-SM", 4, 11),
        ("DIAPER-MD", 12, 23),
        ("DIAPER-LG", 24, 35),
        ("DIAPER-XL", 36, 48),
    ],
    "school-bag": [
        ("BAG-JUNIOR", 48, 107),
        ("BAG-SENIOR", 108, 179),
        ("BAG-FULL", 180, 300),
    ],
}

DEMO_MANUFACTURER_EMAIL = "demo-manufacturer@lifekart.com"
DEMO_MANUFACTURER_PASSWORD = "demo123"


async def seed_all():
    async with AsyncSessionLocal() as db:
        cat_count = await db.execute(select(ProductCategory).limit(1))
        if cat_count.scalar_one_or_none():
            print("Catalog already seeded — skipping")
            return

        # 1. Create demo manufacturer user
        user = User(
            email=DEMO_MANUFACTURER_EMAIL,
            full_name="LifeKart Demo Manufacturer",
            role=UserRole.MANUFACTURER,
            hashed_password=hash_password(DEMO_MANUFACTURER_PASSWORD),
        )
        db.add(user)
        await db.flush()

        manufacturer = Manufacturer(
            user_id=user.id,
            company_name="LifeKart Demo Co.",
            is_verified=True,
        )
        db.add(manufacturer)
        await db.flush()

        print(f"Demo manufacturer created: {DEMO_MANUFACTURER_EMAIL} / {DEMO_MANUFACTURER_PASSWORD}")

        # 2. Create categories
        category_map: dict[str, ProductCategory] = {}
        for name, slug, unit_type, avg_yearly, max_age in CATEGORIES:
            cat = ProductCategory(
                name=name,
                slug=slug,
                unit_type=unit_type,
                avg_lifetime_consumption_per_year=avg_yearly,
                max_age_limit_years=max_age,
            )
            db.add(cat)
            category_map[slug] = cat

        await db.flush()
        print(f"Seeded {len(CATEGORIES)} categories")

        # Track out of stock items for logging
        out_of_stock_count = 0

        # 3. Create sized products and progression rules for age-varying categories
        rules_created = 0
        products_created = 0

        for category_slug, size_rules in PROGRESSION_RULES.items():
            category = category_map.get(category_slug)
            if not category:
                continue

            for sku, start_age, end_age in size_rules:
                existing_product = await db.execute(
                    select(Product).where(Product.sku == sku)
                )
                if existing_product.scalar_one_or_none():
                    continue
                
                # Randomly assign 0 stock (30% chance) or 5000 stock (70% chance)
                assigned_stock = random.choice([0, 0, 0, 5000, 5000, 5000, 5000, 5000, 5000, 5000])
                if assigned_stock == 0:
                    out_of_stock_count += 1

                product = Product(
                    category_id=category.id,
                    manufacturer_id=manufacturer.id,
                    name=f"{category.name} - {sku.split('-')[-1]}",
                    sku=sku,
                    unit_price_wholesale=Decimal("150.00"),
                    unit_price_retail=Decimal("299.00"),
                    is_active=True,
                    stock_quantity=assigned_stock, 
                )
                db.add(product)
                await db.flush()
                products_created += 1

                rule = ProductProgressionRule(
                    category_id=category.id,
                    specific_product_id=product.id,
                    start_age_months=start_age,
                    end_age_months=end_age,
                )
                db.add(rule)
                rules_created += 1

        # 4. Create simple staple products for categories WITHOUT progression rules
        simple_products_created = 0
        
        for name, slug, unit_type, avg_yearly, max_age in CATEGORIES:
            if slug in PROGRESSION_RULES:
                continue
                
            category = category_map.get(slug)
            if not category:
                continue

            sku = f"{slug.upper()}-STD"
            existing_product = await db.execute(
                select(Product).where(Product.sku == sku)
            )
            if existing_product.scalar_one_or_none():
                continue
            
            # Randomly assign 0 stock (30% chance) or 10000 stock (70% chance)
            assigned_stock = random.choice([0, 0, 0, 2000, 8000, 500, 6000, 7000, 1000, 1000])
            if assigned_stock == 0:
                out_of_stock_count += 1

            standard_product = Product(
                category_id=category.id,
                manufacturer_id=manufacturer.id,
                name=f"{name} - Standard",
                sku=sku,
                unit_price_wholesale=Decimal("50.00"),  
                unit_price_retail=Decimal("75.00"),
                is_active=True,
                stock_quantity=assigned_stock,
            )
            db.add(standard_product)
            simple_products_created += 1

        await db.commit()

        print(f"Seeded {products_created} sized products")
        print(f"Seeded {rules_created} progression rules")
        print(f"Seeded {simple_products_created} simple staple products")
        print(f"⚠️ TEST DATA: {out_of_stock_count} products were intentionally seeded with 0 stock.")
        
        print("\nAge-varying categories with progression rules:")
        for cat_slug, rules in PROGRESSION_RULES.items():
            print(f"  {cat_slug}: {len(rules)} sizes → {[r[0] for r in rules]}")


if __name__ == "__main__":
    asyncio.run(seed_all())