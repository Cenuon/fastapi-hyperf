"""V1 API router aggregation."""
from fastapi import APIRouter

from app.api.v1.api_keys import router as api_keys_router
from app.api.v1.auth import router as auth_router
from app.api.v1.rate_limits import router as rate_limits_router
from app.api.v1.tiers import router as tiers_router
from app.api.v1.users import router as users_router

router = APIRouter(prefix="/v1")
router.include_router(users_router, prefix="/users", tags=["Users"])
router.include_router(tiers_router, prefix="/tiers", tags=["Tiers"])
router.include_router(rate_limits_router, prefix="/rate-limits", tags=["Rate Limits"])
router.include_router(api_keys_router, prefix="/api-keys", tags=["API Keys"])
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
