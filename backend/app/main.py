from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1.router import api_router
from app.api.webhooks import router as webhooks_router
from app.database.session import engine, AsyncSessionLocal
from app.database.base import Base
from app.seeds.locations import seed_locations
from app.database.sync import sync_sqlite_schema_sync

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("blood_connect")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Blood Connect API...")
    # In development / SQLite mode, automatically create tables, sync missing columns, and seed locations and users
    if settings.DATABASE_URL.startswith("sqlite"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.run_sync(sync_sqlite_schema_sync)
        async with AsyncSessionLocal() as session:
            await seed_locations(session)
            from app.seeds.users import seed_users
            await seed_users(session)
        logger.info("Initialized local SQLite database and verified locations & sample users/admin.")
    yield
    logger.info("Shutting down Blood Connect API...")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Blood Connect — Donor discovery and connection platform REST API.",
    version="1.0.0",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    lifespan=lifespan
)

# CORS Middleware
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API v1 Router & Webhooks Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(webhooks_router)
app.include_router(webhooks_router, prefix=settings.API_V1_PREFIX)

# Top-level magic link alias: GET /auth/whatsapp
from app.api.v1.auth import redeem_whatsapp_token_get, get_whatsapp_config
app.add_api_route(
    "/auth/whatsapp",
    redeem_whatsapp_token_get,
    methods=["GET"],
    tags=["Authentication"],
    include_in_schema=True
)
app.add_api_route(
    "/auth/whatsapp/config",
    get_whatsapp_config,
    methods=["GET"],
    tags=["Authentication"],
    include_in_schema=True
)

# Top-level legal route aliases
from app.api.v1.legal import (
    get_privacy_policy,
    get_terms_of_service,
    get_data_deletion_instructions,
    meta_data_deletion_callback,
)
app.add_api_route(
    "/privacy-policy",
    get_privacy_policy,
    methods=["GET", "HEAD"],
    tags=["Legal & Compliance"],
    include_in_schema=True
)
app.add_api_route(
    "/privarcy-policy",
    get_privacy_policy,
    methods=["GET", "HEAD"],
    tags=["Legal & Compliance"],
    include_in_schema=False
)
app.add_api_route(
    "/terms",
    get_terms_of_service,
    methods=["GET", "HEAD"],
    tags=["Legal & Compliance"],
    include_in_schema=True
)
app.add_api_route(
    "/terms-of-service",
    get_terms_of_service,
    methods=["GET", "HEAD"],
    tags=["Legal & Compliance"],
    include_in_schema=False
)
app.add_api_route(
    "/data-deletion",
    get_data_deletion_instructions,
    methods=["GET", "HEAD"],
    tags=["Legal & Compliance"],
    include_in_schema=True
)
app.add_api_route(
    "/data-deletion",
    meta_data_deletion_callback,
    methods=["POST"],
    tags=["Legal & Compliance"],
    include_in_schema=False
)
app.add_api_route(
    "/user-data-deletion",
    get_data_deletion_instructions,
    methods=["GET", "HEAD"],
    tags=["Legal & Compliance"],
    include_in_schema=False
)




@app.api_route("/", methods=["GET", "HEAD"], tags=["Root"])
async def root():
    content = {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "online",
        "health": f"{settings.API_V1_PREFIX}/health"
    }
    if not settings.is_production:
        content["documentation"] = "/docs"
    return JSONResponse(content=content)
