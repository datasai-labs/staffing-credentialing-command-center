from __future__ import annotations

from datetime import date
from typing import Optional

from cachetools import TTLCache
from fastapi import APIRouter, HTTPException, Query

from models.common import parse_date
from models.kpis import KpiSummaryDaily
from services import databricks
from services.databricks import DatabricksNotConfigured
from services.queries import kpi_latest_sql
from services import mock_data
from settings import settings

router = APIRouter()

_kpi_cache: TTLCache = TTLCache(maxsize=32, ttl=settings.kpi_cache_ttl_seconds)


@router.get("/kpis", response_model=KpiSummaryDaily)
def get_kpis(as_of_date: Optional[str] = Query(default=None, description="YYYY-MM-DD")) -> KpiSummaryDaily:
    key = as_of_date or "latest"
    if key in _kpi_cache:
        return _kpi_cache[key]

    as_dt = parse_date(as_of_date) if as_of_date else None
    sql_text, params = kpi_latest_sql(as_dt)

    def _run():
        rows = databricks.fetch_all(sql_text, params).rows
        return rows[0] if rows else None

    try:
        item = databricks.with_retry(_run)
    except DatabricksNotConfigured:
        if not settings.use_mock_data:
            raise HTTPException(status_code=503, detail="Databricks not configured (no warehouse/token).")
        parsed = mock_data.mock_kpis()
        _kpi_cache[key] = parsed
        return parsed
    if not item:
        raise ValueError("No KPI rows found")
    parsed = KpiSummaryDaily.model_validate(item)
    _kpi_cache[key] = parsed
    return parsed

