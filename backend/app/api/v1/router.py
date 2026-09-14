from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.donors import router as donors_router
from app.api.v1.locations import router as locations_router
from app.api.v1.requests import router as requests_router
from app.api.v1.notifications import router as notifications_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(auth_router)
api_router.include_router(donors_router)
api_router.include_router(locations_router)
api_router.include_router(requests_router)
api_router.include_router(notifications_router)
