"""
API v1 Router Aggregator
"""
from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.mandates import router as mandates_router
from app.api.v1.ingest import router as ingest_router
from app.api.v1.merchants import router as merchants_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.subscriptions import router as subscriptions_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(mandates_router)
api_v1_router.include_router(ingest_router)
api_v1_router.include_router(merchants_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(subscriptions_router)

