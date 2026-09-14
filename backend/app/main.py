from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1.router import api_router
from app.database.session import engine, AsyncSessionLocal
from app.database.base import Base
from app.seeds.locations import seed_locations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("blood_connect")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Blood Connect API...")
    # In development / SQLite mode, automatically create tables and seed locations if not existing
    if settings.DATABASE_URL.startswith("sqlite"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSessionLocal() as session:
            await seed_locations(session)
        logger.info("Initialized local SQLite database and verified location seeds.")
    yield
    logger.info("Shutting down Blood Connect API...")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Blood Connect — Donor discovery and connection platform REST API.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    return JSONResponse(
        content={
            "name": settings.APP_NAME,
            "version": "1.0.0",
            "documentation": "/docs",
            "health": f"{settings.API_V1_PREFIX}/health"
        }
    )
