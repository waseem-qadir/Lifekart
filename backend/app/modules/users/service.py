import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.modules.users.models import User
from app.modules.users.schemas import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: UserRegisterRequest) -> User:
        existing = await self.db.execute(select(User).where(User.email == data.email))
        if existing.scalar_one_or_none():
            raise ValueError("A user with this email already exists")

        user = User(
            email=data.email,
            phone=data.phone,
            full_name=data.full_name,
            role=data.role,
            hashed_password=hash_password(data.password),
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def login(self, data: UserLoginRequest) -> TokenResponse:
        result = await self.db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("Invalid email or password")
        if not user.is_active:
            raise ValueError("Account is deactivated")
        if not verify_password(data.password, user.hashed_password):
            raise ValueError("Invalid email or password")

        access_token = create_access_token(str(user.id), user.role)
        refresh_token = create_refresh_token(str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60,
            user=UserResponse.model_validate(user),
        )

    async def get_current_user(self, user_id: uuid.UUID) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        return user

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        from app.core.security import verify_refresh_token

        payload = verify_refresh_token(refresh_token)
        user_id = uuid.UUID(payload["sub"])

        user = await self.get_current_user(user_id)
        new_access = create_access_token(str(user.id), user.role)
        new_refresh = create_refresh_token(str(user.id))

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            expires_in=30 * 60,
            user=UserResponse.model_validate(user),
        )

    async def get_user_savings(self, user_id: uuid.UUID) -> dict:
        from app.modules.analytics.service import AnalyticsService
        from app.modules.profiling.models import Household

        result = await self.db.execute(select(Household).where(Household.user_id == user_id))
        household = result.scalar_one_or_none()
        if not household:
            raise ValueError("Household not found. Create your household first.")

        analytics = AnalyticsService(self.db)
        return await analytics.calculate_user_monthly_savings(str(household.id))

    async def list_users(self, role: str | None = None, is_active: bool | None = None, skip: int = 0, limit: int = 50) -> list[User]:
        query = select(User)
        if role:
            query = query.where(User.role == role)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_user_role(self, user_id: uuid.UUID, role: str) -> User:
        user = await self.get_current_user(user_id)
        user.role = role
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user_status(self, user_id: uuid.UUID, is_active: bool) -> User:
        user = await self.get_current_user(user_id)
        user.is_active = is_active
        await self.db.commit()
        await self.db.refresh(user)
        return user