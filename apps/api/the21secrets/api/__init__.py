from fastapi import APIRouter

from the21secrets.api.analytics import router as analytics_router
from the21secrets.api.approvals import router as approvals_router
from the21secrets.api.audit import router as audit_router
from the21secrets.api.ga4 import router as ga4_router
from the21secrets.api.meta import router as meta_router
from the21secrets.api.settings import router as settings_router
from the21secrets.api.system import router as system_router
from the21secrets.auth.router import router as auth_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(system_router)
api_router.include_router(settings_router)
api_router.include_router(audit_router)
api_router.include_router(meta_router)
api_router.include_router(approvals_router)
api_router.include_router(ga4_router)
api_router.include_router(analytics_router)
