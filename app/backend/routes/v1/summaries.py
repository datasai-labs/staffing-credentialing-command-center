from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from models.common import parse_date
from models.summaries import (
    CredentialRiskSummaryResponse,
    KpiTrendResponse,
    ProvidersSummaryResponse,
    ShiftPredictionResponse,
    StaffingSummaryResponse,
)
from services import databricks, mock_data
from services.databricks import DatabricksNotConfigured
from services.queries import (
    credential_risk_summary_sql,
    kpis_trend_sql,
    providers_summary_sql,
    shift_prediction_sql,
    staffing_summary_sql,
)
from settings import settings

router = APIRouter()


@router.get("/kpis/trend", response_model=KpiTrendResponse)
def kpis_trend(days: int = Query(default=30, ge=2, le=365)):
    try:
        sql_text, params = kpis_trend_sql(days)

        def _run():
            rows = databricks.fetch_all(sql_text, params).rows
            # return ascending by date
            return list(reversed(rows))

        rows = databricks.with_retry(_run)
        return KpiTrendResponse(days=days, points=rows)  # pydantic will coerce
    except DatabricksNotConfigured:
        if not settings.use_mock_data:
            raise HTTPException(status_code=503, detail="Databricks not configured (no warehouse/token).")
        return mock_data.mock_kpis_trend(days=days)


@router.get("/staffing_gaps/summary", response_model=StaffingSummaryResponse)
def staffing_summary(
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    facility_id: Optional[str] = None,
    procedure_code: Optional[str] = None,
    risk_level: Optional[str] = Query(default=None, description="Comma-separated: LOW,MEDIUM,HIGH"),
):
    sd: Optional[date] = parse_date(start_date) if start_date else None
    ed: Optional[date] = parse_date(end_date) if end_date else None

    try:
        queries, params = staffing_summary_sql(
            start_date=sd,
            end_date=ed,
            facility_id=facility_id,
            risk_level=risk_level,
            procedure_code=procedure_code,
        )

        def _run():
            by_risk = databricks.fetch_all(queries["by_risk_level"], params).rows
            daily = databricks.fetch_all(queries["daily_gap_count"], params).rows
            top_fac = databricks.fetch_all(queries["top_facilities"], params).rows
            top_proc = databricks.fetch_all(queries["top_procedures"], params).rows
            return by_risk, daily, top_fac, top_proc

        by_risk, daily, top_fac, top_proc = databricks.with_retry(_run)
        return StaffingSummaryResponse(
            by_risk_level=by_risk,
            daily_gap_count=daily,
            top_facilities=top_fac,
            top_procedures=top_proc,
        )
    except DatabricksNotConfigured:
        if not settings.use_mock_data:
            raise HTTPException(status_code=503, detail="Databricks not configured (no warehouse/token).")
        return mock_data.mock_staffing_summary()


@router.get("/credential_risk/summary", response_model=CredentialRiskSummaryResponse)
def credential_risk_summary(
    cred_type: Optional[str] = None,
    risk_bucket: Optional[str] = Query(default=None, description="Comma-separated buckets"),
):
    try:
        queries, params = credential_risk_summary_sql(cred_type=cred_type, risk_bucket=risk_bucket)

        def _run():
            by_bucket = databricks.fetch_all(queries["by_bucket"], params).rows
            by_type = databricks.fetch_all(queries["by_cred_type"], params).rows
            by_week = databricks.fetch_all(queries["expires_by_week"], params).rows
            return by_bucket, by_type, by_week

        by_bucket, by_type, by_week = databricks.with_retry(_run)
        return CredentialRiskSummaryResponse(by_bucket=by_bucket, by_cred_type=by_type, expires_by_week=by_week)
    except DatabricksNotConfigured:
        if not settings.use_mock_data:
            raise HTTPException(status_code=503, detail="Databricks not configured (no warehouse/token).")
        return mock_data.mock_credential_risk_summary()


@router.get("/providers/summary", response_model=ProvidersSummaryResponse)
def providers_summary(
    specialty: Optional[str] = None,
    status: Optional[str] = None,
    expiring_within_days: Optional[int] = Query(default=None, ge=0, le=3650),
):
    try:
        queries, params = providers_summary_sql(specialty=specialty, status=status, expiring_within_days=expiring_within_days)

        def _run():
            by_spec = databricks.fetch_all(queries["by_specialty"], params).rows
            funnel = databricks.fetch_all(queries["expiring_funnel"], params).rows
            hist = databricks.fetch_all(queries["readiness_histogram"], params).rows
            return by_spec, funnel, hist

        by_spec, funnel, hist = databricks.with_retry(_run)
        return ProvidersSummaryResponse(by_specialty=by_spec, expiring_funnel=funnel, readiness_histogram=hist)
    except DatabricksNotConfigured:
        if not settings.use_mock_data:
            raise HTTPException(status_code=503, detail="Databricks not configured (no warehouse/token).")
        return mock_data.mock_providers_summary()


@router.get("/shifts/{shift_id}/prediction", response_model=ShiftPredictionResponse)
def shift_prediction(shift_id: str):
    try:
        sql_text, params = shift_prediction_sql(shift_id)

        def _run():
            rows = databricks.fetch_all(sql_text, params).rows
            return rows[0] if rows else None

        row = databricks.with_retry(_run)
        if not row:
            return ShiftPredictionResponse(shift_id=shift_id)
        return ShiftPredictionResponse.model_validate(row)
    except DatabricksNotConfigured:
        if not settings.use_mock_data:
            raise HTTPException(status_code=503, detail="Databricks not configured (no warehouse/token).")
        return mock_data.mock_shift_prediction(shift_id)

