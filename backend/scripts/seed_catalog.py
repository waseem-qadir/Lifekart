import asyncio
import sys
import os
import random
from decimal import Decimal
from sqlalchemy import select

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app.main

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
    # (name, slug, unit_type, avg_yearly, max_age, description, image_url, avg_savings)
    ("Rice", "rice", "kg", 60, None,
     "Premium basmati, sona masoori, and parboiled rice sourced directly from Punjab and Andhra Pradesh mills.",
     "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=800&q=80", "42%"),
    ("Wheat Flour", "wheat-flour", "kg", 120, None,
     "Whole wheat atta, maida, and sooji — stone-ground and fresh-packed for bulk orders.",
     "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=800&q=80", "35%"),
    ("Toothpaste", "toothpaste", "piece", 12, None,
     "Fluoride, herbal, and whitening toothpaste from top dental brands at wholesale rates.",
     "https://images.unsplash.com/photo-1624454002302-36b824d7bd0a?w=800&q=80", "28%"),
    ("Toothbrush", "toothbrush", "piece", 4, None,
     "Manual and electric toothbrushes with soft, medium, and hard bristle options.",
     "https://images.unsplash.com/photo-1607613009820-a29f7bb81c04?w=800&q=80", "25%"),
    ("Bathing Soap", "bathing-soap", "piece", 24, None,
     "Beauty, glycerin, and antibacterial bathing bars — bulk packs for families and hotels.",
     "https://images.unsplash.com/photo-1556229010-6c3f2c9ca5f8?w=800&q=80", "32%"),
    ("Shampoo", "shampoo", "piece", 12, None,
     "Anti-dandruff, protein, and herbal shampoos in family-size bottles.",
     "https://images.unsplash.com/photo-1535585209827-a15fcdbc4c2d?w=800&q=80", "30%"),
    ("Laundry Detergent", "laundry-detergent", "kg", 24, None,
     "Front-load and top-load powders + liquid detergents — industrial grade for bulk washing.",
     "https://images.unsplash.com/photo-1585421514284-efb74c2b69ba?w=800&q=80", "33%"),
    ("Dishwashing Liquid", "dishwashing-liquid", "piece", 12, None,
     "Lemon, antibacterial, and gel-based dish wash liquids in 500ml to 5L containers.",
     "https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=800&q=80", "27%"),
    ("Cooking Oil", "cooking-oil", "liter", 36, None,
     "Sunflower, mustard, groundnut, and coconut oil — cold-pressed and refined variants available.",
     "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=800&q=80", "38%"),
    ("Sugar", "sugar", "kg", 24, None,
     "Refined white sugar, brown sugar, and jaggery powder for home and commercial kitchens.",
     "https://images.unsplash.com/photo-1531468367001-b8d9db6c3c4e?w=800&q=80", "22%"),
    ("Salt", "salt", "kg", 12, None,
     "Iodised table salt, rock salt, pink Himalayan salt, and black salt — bulk sacks available.",
     "https://images.unsplash.com/photo-1626197031507-c17099753214?w=800&q=80", "18%"),
    ("Tea", "tea", "kg", 6, None,
     "Assam, Darjeeling, and Nilgiri loose-leaf tea + premium dust for chai — sourced from estates.",
     "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=800&q=80", "35%"),
    ("Coffee", "coffee", "kg", 4, None,
     "Filter coffee, instant, and espresso blends — South Indian plantation fresh.",
     "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=800&q=80", "31%"),
    ("Milk", "milk", "liter", 365, None,
     "Full-cream, toned, and double-toned milk — daily delivery with cold-chain integrity.",
     "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=800&q=80", "20%"),
    ("Curd/Yogurt", "curd-yogurt", "liter", 180, None,
     "Fresh-set curd and probiotic yogurt — delivered in reusable glass bottles.",
     "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=800&q=80", "24%"),
    ("Butter", "butter", "kg", 12, None,
     "Salted, unsalted, and white butter blocks — Amul, Mother Dairy, and local cooperative brands.",
     "https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=800&q=80", "19%"),
    ("Cheese", "cheese", "kg", 6, None,
     "Cheddar, mozzarella, processed slices, and paneer blocks — bulk restaurant packs.",
     "https://images.unsplash.com/photo-1452195105486-e820edf1b5b4?w=800&q=80", "26%"),
    ("Eggs", "eggs", "piece", 360, None,
     "Farm-fresh white and brown eggs — graded, tray-packed, and cold-chain delivered.",
     "https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=800&q=80", "15%"),
    ("Chicken", "chicken", "kg", 24, None,
     "Halal-cut, free-range, and antibiotic-free chicken — whole bird and boneless cuts.",
     "https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=800&q=80", "22%"),
    ("Fish", "fish", "kg", 12, None,
     "Freshwater and marine catch — cleaned, portioned, and vacuum-sealed for doorstep delivery.",
     "https://images.unsplash.com/photo-1615141982883-c7ad0e69fd62?w=800&q=80", "28%"),
    ("Lentils (Dal)", "lentils-dal", "kg", 36, None,
     "Toor, moong, masoor, urad, and chana dal — split, whole, and polished varieties.",
     "https://images.unsplash.com/photo-1515543904379-3d757afe72e4?w=800&q=80", "40%"),
    ("Chickpeas", "chickpeas", "kg", 12, None,
     "Kabuli and desi chickpeas — premium export-grade sorted and cleaned.",
     "https://images.unsplash.com/photo-1598515214211-89d3c73ae83b?w=800&q=80", "34%"),
    ("Kidney Beans", "kidney-beans", "kg", 12, None,
     "Red kidney beans (rajma) — Jammu-sourced, slow-cook variety at bulk pricing.",
     "https://images.unsplash.com/photo-1551462147-ff29053bfc14?w=800&q=80", "36%"),
    ("Onions", "onions", "kg", 60, None,
     "Nasik red onions — sorted by size, stored in cold rooms, delivered weekly.",
     "https://images.unsplash.com/photo-1618512496248-a01fe22aa0a8?w=800&q=80", "45%"),
    ("Potatoes", "potatoes", "kg", 72, None,
     "Fresh table potatoes from UP and Punjab — large, medium, and baby sizes.",
     "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=800&q=80", "42%"),
    ("Tomatoes", "tomatoes", "kg", 48, None,
     "Hybrid and country tomatoes — ripened on the vine, sorted by grade.",
     "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=800&q=80", "38%"),
    ("Garlic", "garlic", "kg", 6, None,
     "Single-clove and multi-clove garlic — sourced from MP and Rajasthan farms.",
     "https://images.unsplash.com/photo-1615477550927-6ec8445fcf13?w=800&q=80", "28%"),
    ("Ginger", "ginger", "kg", 6, None,
     "Fresh root ginger — firm, fiberless variety with extended shelf life.",
     "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=800&q=80", "25%"),
    ("Green Chillies", "green-chillies", "kg", 6, None,
     "Medium-spice and hot varieties — sourced fresh daily from local mandis.",
     "https://images.unsplash.com/photo-1583119022894-919a68a3d0e3?w=800&q=80", "30%"),
    ("Coriander Leaves", "coriander-leaves", "pack", 24, None,
     "Fresh dhania patta — bunched and cold-packed for extended freshness.",
     "https://images.unsplash.com/photo-1600231916623-1e73f3a3b6f4?w=800&q=80", "20%"),
    ("Bananas", "bananas", "kg", 48, None,
     "Yelakki, robusta, and nendran varieties — ethylene-ripened, graded by size.",
     "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=800&q=80", "33%"),
    ("Apples", "apples", "kg", 24, None,
     "Shimla, Kinnaur, and Washington apples — cold-stored and crisp on arrival.",
     "https://images.unsplash.com/photo-1570913149827-d2ac84ab3f9a?w=800&q=80", "30%"),
    ("Oranges", "oranges", "kg", 24, None,
     "Nagpur santra and Darjeeling mandarin — juicy, sweet, and pesticide-controlled.",
     "https://images.unsplash.com/photo-1611080626919-7cf5a9dbab5b?w=800&q=80", "27%"),
    ("Bread", "bread", "pack", 180, None,
     "White, brown, and multigrain sandwich bread + pav and bun variants — delivered fresh daily.",
     "https://images.unsplash.com/photo-1549931319-a545799f6a45?w=800&q=80", "18%"),
    ("Breakfast Cereal", "breakfast-cereal", "kg", 12, None,
     "Corn flakes, muesli, oats, and granola — family packs at wholesale prices.",
     "https://images.unsplash.com/photo-1524326885831-f1145704d2a9?w=800&q=80", "29%"),
    ("Biscuits", "biscuits", "pack", 48, None,
     "Marie, digestive, cream, and glucose biscuits — multi-pack combos for offices and homes.",
     "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=800&q=80", "24%"),
    ("Jam", "jam", "kg", 6, None,
     "Mixed fruit, strawberry, mango, and orange marmalade — bulk jars for hotels and canteens.",
     "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=800&q=80", "21%"),
    ("Peanut Butter", "peanut-butter", "kg", 4, None,
     "Crunchy and creamy natural peanut butter — no palm oil, high-protein.",
     "https://images.unsplash.com/photo-1603105026260-be19cf5e4b12?w=800&q=80", "26%"),
    ("Spices - Turmeric", "spices-turmeric", "kg", 2, None,
     "Salem and Nizamabad turmeric — high curcumin, polished and unpolished.",
     "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=800&q=80", "48%"),
    ("Spices - Red Chilli", "spices-red-chilli", "kg", 2, None,
     "Guntur and Byadagi chillies — whole, crushed, and powdered at source.",
     "https://images.unsplash.com/photo-1589906493606-e7e0c99c0f0b?w=800&q=80", "45%"),
    ("Spices - Cumin", "spices-cumin", "kg", 2, None,
     "Jeera from Gujarat and Rajasthan — bold seeds with high essential oil content.",
     "https://images.unsplash.com/photo-1599909651206-6a5c8e4e1e5c?w=800&q=80", "52%"),
    ("Spices - Coriander", "spices-coriander", "kg", 2, None,
     "Dhania whole and powdered — split, bold seeds from Kota region.",
     "https://images.unsplash.com/photo-1620574387735-3624d75b2dbc?w=800&q=80", "44%"),
    ("Spices - Garam Masala", "spices-garam-masala", "kg", 2, None,
     "Traditional and premium garam masala blends — whole spices dry-roasted and ground.",
     "https://images.unsplash.com/photo-1567351514435-f9f40ecc9f2e?w=800&q=80", "50%"),
    ("Tissue Paper", "tissue-paper", "pack", 48, None,
     "2-ply and 3-ply facial tissues + kitchen roll — soft, absorbent, bulk cartons.",
     "https://images.unsplash.com/photo-1583947215259-38e31be8751f?w=800&q=80", "22%"),
    ("Aluminum Foil", "aluminum-foil", "pack", 6, None,
     "Food-grade aluminum foil rolls — 25m and 50m lengths for kitchens and catering.",
     "https://images.unsplash.com/photo-1662546471686-afcbbeb4faee?w=800&q=80", "19%"),
    ("Plastic Wrap", "plastic-wrap", "pack", 6, None,
     "Cling film and stretch wrap — microwave-safe, commercial-length rolls.",
     "https://images.unsplash.com/photo-1603194634843-4f7b77e1ea8c?w=800&q=80", "17%"),
    ("Garbage Bags", "garbage-bags", "pack", 24, None,
     "Biodegradable and heavy-duty black garbage bags — small to jumbo sizes.",
     "https://images.unsplash.com/photo-1605600659908-0eff719bca1f?w=800&q=80", "20%"),
    ("School Uniform", "school-uniform", "piece", 3, 18,
     "Stitched and unstitched uniform sets — cotton-poly blend, pre-shrunk fabric.",
     "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=800&q=80", "28%"),
    ("School Shoes", "school-shoes", "pair", 2, 18,
     "Black leather and canvas school shoes — Bata, Liberty, and local quality brands.",
     "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&q=80", "25%"),
    ("School Bag", "school-bag", "piece", 1, 18,
     "Ergonomic backpacks with water bottle pocket — junior, senior, and college sizes.",
     "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&q=80", "22%"),
    ("Notebooks", "notebooks", "piece", 24, 22,
     "Hardbound, softbound, and spiral notebooks — ruled, unruled, and practical sheets.",
     "https://images.unsplash.com/photo-1531346878377-a5be20888e57?w=800&q=80", "18%"),
    ("Pens & Pencils", "pens-pencils", "pack", 12, 22,
     "Ball pens, gel pens, and HB pencils — bulk classroom packs at distributor rates.",
     "https://images.unsplash.com/photo-1513542789411-b6a5d4f31634?w=800&q=80", "15%"),
    ("Diapers", "diapers", "pack", 360, 4,
     "Newborn to XL tape and pant-style diapers — super-absorbent, 12-hour protection.",
     "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=800&q=80", "35%"),
    ("Baby Wipes", "baby-wipes", "pack", 120, 4,
     "Alcohol-free, aloe-enriched baby wipes — 72-count and 144-count packs.",
     "https://images.unsplash.com/photo-1555252333-9f8e92e65df9?w=800&q=80", "28%"),
    ("Baby Food", "baby-food", "kg", 24, 4,
     "Stage 1 to 4 infant cereals, purees, and formula — FSSAI certified, no preservatives.",
     "https://images.unsplash.com/photo-1584833753959-e3d7a23b11b9?w=800&q=80", "30%"),
    ("Pet Food - Dog", "pet-food-dog", "kg", 48, None,
     "Puppy, adult, and senior dry kibble — chicken and vegetarian formulas.",
     "https://images.unsplash.com/photo-1568640347023-a616a30bc3bd?w=800&q=80", "24%"),
    ("Pet Food - Cat", "pet-food-cat", "kg", 36, None,
     "Wet and dry cat food — tuna, salmon, and chicken flavors with taurine.",
     "https://images.unsplash.com/photo-1589924691995-400dc5612341?w=800&q=80", "22%"),
    ("Mineral Water", "mineral-water", "liter", 180, None,
     "Bisleri, Kinley, and local ISI-certified packaged drinking water — 1L, 2L, and 20L jars.",
     "https://images.unsplash.com/photo-1523362628745-0c100150b854?w=800&q=80", "12%"),
    ("Soft Drinks", "soft-drinks", "liter", 24, None,
     "Cola, lemon, and orange carbonated beverages — 200ml to 2L bottles.",
     "https://images.unsplash.com/photo-1554866585-cd94860890b7?w=800&q=80", "16%"),
    ("Juice", "juice", "liter", 24, None,
     "Mango, apple, mixed fruit, and pomegranate juices — tetra pack and PET bottles.",
     "https://images.unsplash.com/photo-1622597467836-f3285f2131b8?w=800&q=80", "20%"),
    ("Hand Wash", "hand-wash", "piece", 12, None,
     "Antibacterial and moisturizing liquid hand wash — 250ml to 5L refill packs.",
     "https://images.unsplash.com/photo-1584306678672-1d1c4c9d4e05?w=800&q=80", "25%"),
    ("Floor Cleaner", "floor-cleaner", "liter", 6, None,
     "Pine, citrus, and floral floor disinfectants — concentrated, dilution 1:50.",
     "https://images.unsplash.com/photo-1585421514284-efb74c2b69ba?w=800&q=80", "30%"),
    ("Surface Disinfectant", "surface-disinfectant", "liter", 6, None,
     "Hospital-grade quaternary ammonium and alcohol-based surface sanitizers.",
     "https://images.unsplash.com/photo-1584744982491-6652b3d4dd02?w=800&q=80", "28%"),
    ("Toilet Cleaner", "toilet-cleaner", "liter", 6, None,
     "Thick bleach and acid-based toilet bowl cleaners — removes rust and hard water stains.",
     "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=800&q=80", "22%"),
    ("Sanitary Pads", "sanitary-pads", "pack", 72, None,
     "Ultra-thin, XXL, and maternity pads — cottony-soft top sheet, wings, 280-320mm.",
     "https://images.unsplash.com/photo-1584306678672-1d1c4c9d4e05?w=800&q=80", "32%"),
    ("Razors", "razors", "piece", 52, None,
     "3-blade and 5-blade disposable razors + cartridge refills — bulk packs for gents and ladies.",
     "https://images.unsplash.com/photo-1626785774573-4b799315345d?w=800&q=80", "26%"),
    ("Shaving Cream", "shaving-cream", "piece", 6, None,
     "Foam, gel, and cream-based shaving lubricants — brushless and traditional lather.",
     "https://images.unsplash.com/photo-1624454002302-36b824d7bd0a?w=800&q=80", "24%"),
    ("Deodorant", "deodorant", "piece", 12, None,
     "Roll-on and spray deodorants — no-gas, long-lasting, antiperspirant formulas.",
     "https://images.unsplash.com/photo-1617897903246-719242758050?w=800&q=80", "22%"),
    ("Sunscreen", "sunscreen", "piece", 6, None,
     "SPF 30, 50, and 70 lotions and gels — water-resistant, dermatologist-tested.",
     "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=800&q=80", "20%"),
    ("Moisturizer", "moisturizer", "piece", 6, None,
     "Day and night creams — aloe, vitamin E, and hyaluronic acid variants.",
     "https://images.unsplash.com/photo-1556229010-6c3f2c9ca5f8?w=800&q=80", "23%"),
    ("Lip Balm", "lip-balm", "piece", 6, None,
     "SPF 15, tinted, and medicated lip balms — petroleum jelly and beeswax bases.",
     "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=800&q=80", "15%"),
    ("Hair Oil", "hair-oil", "piece", 6, None,
     "Coconut, almond, amla, and bhringraj hair oils — cold-pressed and infused.",
     "https://images.unsplash.com/photo-1535585209827-a15fcdbc4c2d?w=800&q=80", "28%"),
    ("Cotton Swabs", "cotton-swabs", "pack", 12, None,
     "100% pure cotton earbuds with paper and plastic stems — 200-count and 500-count boxes.",
     "https://images.unsplash.com/photo-1607613009820-a29f7bb81c04?w=800&q=80", "10%"),
    ("First-Aid Bandages", "first-aid-bandages", "pack", 6, None,
     "Waterproof, fabric, and antiseptic adhesive bandages — assorted sizes in bulk boxes.",
     "https://images.unsplash.com/photo-1583394835485-b1f72ef0e5d1?w=800&q=80", "20%"),
    ("Multivitamin Tablets", "multivitamin-tablets", "pack", 12, None,
     "A-Z multivitamin with minerals — 60 and 120 tablet strips for daily family use.",
     "https://images.unsplash.com/photo-1584308666744-24d8b8e74e54?w=800&q=80", "35%"),
    ("Protein Powder", "protein-powder", "kg", 6, None,
     "Whey, pea, and soy protein isolates — unflavored and chocolate/vanilla variants.",
     "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=800&q=80", "38%"),
    ("Pasta", "pasta", "kg", 12, None,
     "Penne, fusilli, spaghetti, and macaroni — durum wheat, bronze-die extruded.",
     "https://images.unsplash.com/photo-1551462147-ff29053bfc14?w=800&q=80", "27%"),
    ("Noodles", "noodles", "kg", 12, None,
     "Instant and hakka noodles — wheat and atta variants in bulk catering packs.",
     "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?w=800&q=80", "24%"),
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

        category_map: dict[str, ProductCategory] = {}
        for name, slug, unit_type, avg_yearly, max_age, description, image_url, avg_savings in CATEGORIES:
            cat = ProductCategory(
                name=name,
                slug=slug,
                unit_type=unit_type,
                avg_lifetime_consumption_per_year=avg_yearly,
                max_age_limit_years=max_age,
                description=description,
                image_url=image_url,
                avg_savings=avg_savings,
            )
            db.add(cat)
            category_map[slug] = cat

        await db.flush()
        print(f"Seeded {len(CATEGORIES)} categories")

        out_of_stock_count = 0
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

                assigned_stock = random.choice([0, 0, 0, 5000, 5000, 5000, 5000, 5000, 5000, 5000])
                if assigned_stock == 0:
                    out_of_stock_count += 1

                wholesale = round(random.uniform(50.0, 200.0), 2)
                retail = round(wholesale * random.uniform(1.2, 1.8), 2)
                
                product = Product(
                    category_id=category.id,
                    manufacturer_id=manufacturer.id,
                    name=f"{category.name} - {sku.split('-')[-1]}",
                    sku=sku,
                    unit_price_wholesale=Decimal(str(wholesale)),
                    unit_price_retail=Decimal(str(retail)),
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

        simple_products_created = 0

        for name, slug, unit_type, avg_yearly, max_age, description, image_url, avg_savings in CATEGORIES:
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

            assigned_stock = random.choice([0, 0, 0, 2000, 8000, 500, 6000, 7000, 1000, 1000])
            if assigned_stock == 0:
                out_of_stock_count += 1

            wholesale = round(random.uniform(20.0, 100.0), 2)
            retail = round(wholesale * random.uniform(1.2, 1.8), 2)
            
            standard_product = Product(
                category_id=category.id,
                manufacturer_id=manufacturer.id,
                name=f"{name} - Standard",
                sku=sku,
                unit_size=unit_type,
                unit_price_wholesale=Decimal(str(wholesale)),
                unit_price_retail=Decimal(str(retail)),
                is_active=True,
                stock_quantity=assigned_stock,
            )
            db.add(standard_product)
            simple_products_created += 1

        await db.commit()

        print(f"Seeded {products_created} sized products")
        print(f"Seeded {rules_created} progression rules")
        print(f"Seeded {simple_products_created} simple staple products")
        print(f"TEST DATA: {out_of_stock_count} products were intentionally seeded with 0 stock.")

        print("\nAge-varying categories with progression rules:")
        for cat_slug, rules in PROGRESSION_RULES.items():
            print(f"  {cat_slug}: {len(rules)} sizes → {[r[0] for r in rules]}")


if __name__ == "__main__":
    asyncio.run(seed_all())