"""
ISORA API - FastAPI Backend
ISMS Operations & Risk Assurance Platform
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.api.v1.router import api_router
from src.api.websocket import websocket_router
from src.db.database import init_db, async_session_maker
from src.db.seed import run_seed
from src.middleware.tenant_middleware import TenantMiddleware
from src.middleware.rate_limit_middleware import RateLimitMiddleware
from src.core.redis import RedisManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()

    # Seed database with initial data
    async with async_session_maker() as db:
        try:
            await run_seed(db)
        except Exception as e:
            print(f"Seed error (may be already seeded): {e}")

    yield
    # Shutdown
    await RedisManager.close()


app = FastAPI(
    title="ISORA API",
    version="2.0.0",
    description="ISMS Operations & Risk Assurance Platform",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limit middleware - must be added before tenant middleware
# Note: Middleware executes in reverse order of registration
app.add_middleware(RateLimitMiddleware)

# Tenant middleware - extracts tenant context from JWT
app.add_middleware(TenantMiddleware)

# Include routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(websocket_router, prefix="/api/v1/ws")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "ISORA API",
        "version": "2.0.0",
        "docs": "/api/docs",
    }
