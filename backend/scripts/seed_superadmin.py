import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app.main  # ensure all models are imported and registered
from app.db.session import AsyncSessionLocal
from app.modules.users.models import User, UserRole
from app.core.security import hash_password
from sqlalchemy import select


async def seed_superadmin():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.role == UserRole.SUPERADMIN))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Superadmin already exists: {existing.email}")
            return

        admin = User(
            email="dev@lifekart.com",
            phone="9999999999",
            full_name="Super Admin",
            role=UserRole.SUPERADMIN,
            hashed_password=hash_password("admin123"),
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        print(f"Superadmin created: {admin.email} / admin123")
        print(f"ID: {admin.id}")


if __name__ == "__main__":
    asyncio.run(seed_superadmin())