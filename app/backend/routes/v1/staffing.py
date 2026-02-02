from __future__ import annotations

import json
from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from models.common import PageResponse, parse_date
from models.providers import ProviderMini
from models.staffing import ShiftRecommendations, StaffingGap
from routes.v1._dbx import dbx_or_mock
from services import databricks
from services import mock_data
from services.queries import (
    fq_gold,
    shift_recommendations_sql,
    staffing_gaps_list_sql,
)
from services.eligibility import Assumptions, explain_provider_readiness
from models.eligibility import ShiftEligibilityExplainResponse, EligibilityProviderExplain

router = APIRouter()


@router.get("/staffing_gaps", response_model=PageResponse[StaffingGap])
def list_staffing_gaps(
    start_date: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    facility_id: Optional[str] = None,
    risk_level: Optional[str] = Query(default=None, description="Comma-separated: LOW,MEDIUM,HIGH"),
    procedure_code: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    sort: Optional[str] = Query(default=None, description="field:asc|desc"),
):
    sd = parse_date(start_date) if start_date else None
    ed = parse_date(end_date) if end_date else None
    data_sql, count_sql, params = staffing_gaps_list_sql(
        start_date=sd,
        end_date=ed,
        facility_id=facility_id,
        risk_level=risk_level,
        procedure_code=procedure_code,
        page=page,
        page_size=page_size,
        sort=sort,
    )

    def _run():
        return databricks.fetch_paged(data_sql, count_sql, params)

    def _mock():
        all_items = mock_data.mock_staffing_gaps()
        items = all_items
        if facility_id:
            items = [r for r in items if r.facility_id == facility_id]
        if procedure_code:
            items = [r for r in items if r.required_procedure_code == procedure_code]
        if risk_level:
            allowed = {x.strip() for x in risk_level.split(",") if x.strip()}
            items = [r for r in items if r.risk_level in allowed]
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return (items[start:end], total)
 
    rows, total = dbx_or_mock(lambda: databricks.with_retry(_run), _mock)
    items = [StaffingGap.model_validate(r) for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/shifts/{shift_id}/recommendations", response_model=ShiftRecommendations)
def get_shift_recommendations(shift_id: str, include_providers: bool = Query(default=True)):
    sql_text, params = shift_recommendations_sql(shift_id)

    def _run():
        rows = databricks.fetch_all(sql_text, params).rows
        return rows[0] if rows else None

    row = dbx_or_mock(
        lambda: (databricks.with_retry(_run) or {"shift_id": shift_id, "recommended_provider_ids": []}),
        lambda: mock_data.mock_shift_recommendations(shift_id),
    )
    if isinstance(row, ShiftRecommendations):
        return row
    rec_ids = row.get("recommended_provider_ids") or []

    # Databricks SQL may return arrays as Python lists, or strings. Normalize.
    if isinstance(rec_ids, str):
        try:
            rec_ids = json.loads(rec_ids)
        except Exception:  # noqa: BLE001
            rec_ids = []

    rec_providers: Optional[list[ProviderMini]] = None
    if include_providers and rec_ids:
        # Fetch provider minis via provider_360_flat filtered by ids.
        placeholders = ", ".join([f":pid{i}" for i in range(len(rec_ids))])
        params2 = {f"pid{i}": pid for i, pid in enumerate(rec_ids)}
        sql2 = (
            f"SELECT provider_id, provider_name, specialty, provider_status"
            f" FROM {fq_gold('provider_360_flat')}"
            f" WHERE provider_id IN ({placeholders})"
        )

        def _run2():
            return databricks.fetch_all(sql2, params2).rows

        rows2 = databricks.with_retry(_run2)
        rec_providers = [ProviderMini.model_validate(r) for r in rows2]

    return ShiftRecommendations(shift_id=shift_id, recommended_provider_ids=list(rec_ids), recommended_providers=rec_providers)


@router.get("/shifts/{shift_id}/eligibility_explain", response_model=ShiftEligibilityExplainResponse)
def shift_eligibility_explain(shift_id: str):
    """
    Explain recommended providers for a shift: why eligible / why not eligible.
    Derived only from gold.shift_recommendations + gold.provider_360_flat.
    """
    sql_text, params = shift_recommendations_sql(shift_id)

    def _run():
        rows = databricks.fetch_all(sql_text, params).rows
        return rows[0] if rows else None

    row = dbx_or_mock(lambda: (databricks.with_retry(_run) or {"shift_id": shift_id, "recommended_provider_ids": []}), lambda: mock_data.mock_shift_recommendations(shift_id))
    if isinstance(row, ShiftRecommendations):
        rec_ids = row.recommended_provider_ids
    else:
        rec_ids = row.get("recommended_provider_ids") or []
        if isinstance(rec_ids, str):
            try:
                rec_ids = json.loads(rec_ids)
            except Exception:  # noqa: BLE001
                rec_ids = []
    rec_ids = [str(x) for x in rec_ids if x is not None]

    # Fetch provider 360 rows for the recommended ids
    providers_by_id: dict[str, dict] = {}
    if rec_ids:
        placeholders = ", ".join([f":pid{i}" for i in range(len(rec_ids))])
        params2 = {f"pid{i}": pid for i, pid in enumerate(rec_ids)}
        sql2 = (
            "SELECT provider_id, provider_name, specialty, provider_status, home_facility_id, home_facility_name, "
            "state_license_status, state_license_days_left, acls_status, acls_days_left, active_privilege_count, active_payer_count "
            f"FROM {fq_gold('provider_360_flat')} "
            f"WHERE provider_id IN ({placeholders})"
        )

        def _run2():
            return databricks.fetch_all(sql2, params2).rows

        rows2 = dbx_or_mock(lambda: databricks.with_retry(_run2), lambda: [p.model_dump() for p in mock_data.mock_providers() if p.provider_id in set(rec_ids)])
        providers_by_id = {str(r.get("provider_id")): dict(r) for r in rows2}

    providers: list[EligibilityProviderExplain] = []
    for pid in rec_ids:
        r = providers_by_id.get(pid)
        if not r:
            providers.append(
                EligibilityProviderExplain(
                    provider_id=pid,
                    is_eligible=False,
                    why_not=["Provider not found in provider_360_flat"],
                    why_eligible=[],
                    time_to_ready_days=None,
                )
            )
            continue
        providers.append(explain_provider_readiness(r, assumptions=Assumptions.empty()))

    return ShiftEligibilityExplainResponse(shift_id=shift_id, recommended_provider_ids=rec_ids, providers=providers)

