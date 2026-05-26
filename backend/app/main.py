from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import engine
from app.db.base import Base
from app.modules.users.models import User
from app.modules.catalog.models import ProductCategory, Manufacturer, Product, ProductSubstitute, ProductProgressionRule
from app.modules.profiling.models import Household, Member
from app.modules.calculator.models import LifetimeSubscription
from app.modules.agreements.models import WholesaleAgreement, AgreementItem
from app.modules.scheduling.models import DeliveryEvent, PriceHistory, PriceProtectionRule, SubstitutionEvent, PriceCeilingAlert
from app.modules.payments.models import PaymentMethod, Invoice, PaymentTransaction, WebhookEvent
from app.modules.gifting.models import GiftOrder, GiftOrderItem
from app.modules.corporate.models import CorporatePartner, EmployeeEnrollment
from app.modules.payroll.models import PayrollDeduction
from app.modules.community.models import CommunityGroup, CommunityMembership, CommunityOrder
from app.modules.health.models import HealthProfile, HealthTransition, HealthRule
from app.modules.legacy.models import LegacyNominee, LegacyActivation
from app.core.settings_model import SystemSetting
from app.modules.analytics.models import PlatformMetricsSnapshot
from app.modules.users.router import router as users_router
from app.modules.catalog.router import router as catalog_router
from app.modules.profiling.router import router as profiling_router
from app.modules.calculator.router import router as calculator_router
from app.modules.agreements.router import router as agreements_router
from app.modules.price_protect.router import router as price_protect_router
from app.modules.payments.router import router as payments_router
from app.modules.gifting.router import router as gifting_router
from app.modules.corporate.router import router as corporate_router
from app.modules.payroll.router import router as payroll_router
from app.modules.community.router import router as community_router
from app.modules.health.router import router as health_router
from app.modules.legacy.router import router as legacy_router
from app.modules.analytics.router import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="LifeKart API",
    description="Lifetime Wholesale Buying Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(users_router, prefix="/api/v1", tags=["auth"])
app.include_router(catalog_router, prefix="/api/v1", tags=["catalog"])
app.include_router(profiling_router, prefix="/api/v1", tags=["profiling"])
app.include_router(calculator_router, prefix="/api/v1", tags=["subscriptions"])
app.include_router(agreements_router, prefix="/api/v1", tags=["agreements"])
app.include_router(price_protect_router, prefix="/api/v1", tags=["price-protection"])
app.include_router(payments_router, prefix="/api/v1", tags=["payments"])
app.include_router(gifting_router, prefix="/api/v1", tags=["gifting"])
app.include_router(corporate_router, prefix="/api/v1", tags=["corporate"])
app.include_router(payroll_router, prefix="/api/v1", tags=["payroll"])
app.include_router(community_router, prefix="/api/v1", tags=["community"])
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(legacy_router, prefix="/api/v1", tags=["legacy"])
app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "lifekart"}