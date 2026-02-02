from __future__ import annotations

import logging
import os
import pathlib
import uuid

import orjson
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from routes.v1 import router as v1_router
from services.databricks import DatabricksPermissionError
from settings import settings


class ORJSONResponse(JSONResponse):
    def render(self, content) -> bytes:  # type: ignore[override]
        return orjson.dumps(content, option=orjson.OPT_NON_STR_KEYS)


def configure_logging() -> None:
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))


configure_logging()
logger = logging.getLogger("app")

app = FastAPI(default_response_class=ORJSONResponse)
app.include_router(v1_router)

logger.info(
    "Config: app_env=%s use_mock_data=%s dbx_host_set=%s dbx_http_path_set=%s dbx_token_set=%s catalog=%s schema_gold=%s",
    settings.app_env,
    settings.use_mock_data,
    bool(settings.databricks_server_hostname),
    bool(settings.databricks_http_path),
    bool(settings.databricks_access_token),
    settings.databricks_catalog,
    settings.databricks_schema_gold,
)

origins = settings.cors_origins_list()
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    req_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = req_id
    response = await call_next(request)
    response.headers["x-request-id"] = req_id
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):  # noqa: BLE001
    req_id = getattr(request.state, "request_id", None)
    logger.exception("Unhandled exception", extra={"request_id": req_id, "path": str(request.url.path)})
    return JSONResponse(status_code=500, content={"message": "Internal server error", "request_id": req_id})


@app.exception_handler(DatabricksPermissionError)
async def databricks_permission_handler(request: Request, exc: DatabricksPermissionError):
    req_id = getattr(request.state, "request_id", None)
    # Keep details short; the full SQLSTATE is still logged by the exception logger when it occurs.
    msg = str(exc)
    msg = msg.split("\n")[0][:300]
    return JSONResponse(
        status_code=403,
        content={
            "message": "Databricks permission error (Unity Catalog).",
            "details": msg,
            "request_id": req_id,
            "hint": "Grant the app service principal USE CATALOG on the catalog and USE SCHEMA + SELECT on the gold tables.",
        },
    )


# Serve built frontend (single deployable)
FRONTEND_DIR = pathlib.Path(__file__).resolve().parents[1] / "frontend"
DIST_DIR = FRONTEND_DIR / "dist"

if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")


@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    # API routes should not be handled here
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"message": "Not found"})

    index_path = DIST_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))

    # Dev / not built yet
    return JSONResponse(
        status_code=200,
        content={
            "message": "Frontend not built. Run `cd app/frontend && npm install && npm run build`.",
            "app_env": settings.app_env,
        },
    )

