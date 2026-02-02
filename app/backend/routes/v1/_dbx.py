from __future__ import annotations

from typing import Callable, TypeVar

from fastapi import HTTPException

from services.databricks import DatabricksNotConfigured
from settings import settings

T = TypeVar("T")


def _no_dbx() -> None:
    """
    Standard behavior: in prod (ALLOW_MOCK_DATA=false), fail loudly if Databricks isn't configured.
    In dev/local, callers can fall back to mock data.
    """
    if not settings.use_mock_data:
        raise HTTPException(status_code=503, detail="Databricks not configured (no warehouse/token).")


def dbx_or_mock(run: Callable[[], T], mock: Callable[[], T]) -> T:
    try:
        return run()
    except DatabricksNotConfigured:
        _no_dbx()
        return mock()

