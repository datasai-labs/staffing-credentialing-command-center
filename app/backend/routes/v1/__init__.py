from fastapi import APIRouter

from routes.v1.credentials import router as credentials_router
from routes.v1.healthcheck import router as healthcheck_router
from routes.v1.kpis import router as kpis_router
from routes.v1.providers import router as providers_router
from routes.v1.staffing import router as staffing_router
from routes.v1.summaries import router as summaries_router
from routes.v1.actions import router as actions_router
from routes.v1.worklists import router as worklists_router
from routes.v1.scenario import router as scenario_router
from routes.v1.nurse_staffing import router as nurse_staffing_router

router = APIRouter(prefix="/api/v1")
router.include_router(healthcheck_router, tags=["healthcheck"])
router.include_router(kpis_router, tags=["kpis"])
router.include_router(staffing_router, tags=["staffing"])
router.include_router(credentials_router, tags=["credentials"])
# IMPORTANT: register summary routes before dynamic routes like /providers/{provider_id}
# so /providers/summary isn't treated as provider_id="summary".
router.include_router(summaries_router, tags=["summaries"])
router.include_router(providers_router, tags=["providers"])
router.include_router(actions_router, tags=["actions"])
router.include_router(worklists_router, tags=["worklists"])
router.include_router(scenario_router, tags=["scenario"])
router.include_router(nurse_staffing_router, tags=["nurse_staffing"])

