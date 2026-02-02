from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter

from models.scenario import ScenarioCoverageRequest, ScenarioCoverageResponse, ScenarioShiftResult
from routes.v1._dbx import dbx_or_mock
from services import databricks, mock_data
from services.eligibility import Assumptions, explain_provider_readiness, unique_ids
from services.queries import shift_recommendations_by_ids_sql

router = APIRouter()


def _normalize_recommended_ids(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if x is not None]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(x) for x in parsed if x is not None]
        except Exception:  # noqa: BLE001
            return []
    return []


def _provider_rows_by_id(provider_ids: list[str]) -> dict[str, dict]:
    if not provider_ids:
        return {}
    placeholders = ", ".join([f":pid{i}" for i in range(len(provider_ids))])
    params = {f"pid{i}": pid for i, pid in enumerate(provider_ids)}
    sql_text = (
        "SELECT provider_id, provider_name, specialty, provider_status, home_facility_id, home_facility_name, "
        "state_license_status, state_license_days_left, acls_status, acls_days_left, active_privilege_count, active_payer_count "
        f"FROM {databricks_table_provider_360()} "
        f"WHERE provider_id IN ({placeholders})"
    )
    rows = databricks.fetch_all(sql_text, params).rows
    return {str(r.get("provider_id")): r for r in rows}


def databricks_table_provider_360() -> str:
    from services.queries import fq_gold

    return fq_gold("provider_360_flat")


@router.post("/scenario/coverage", response_model=ScenarioCoverageResponse)
def scenario_coverage(payload: ScenarioCoverageRequest) -> ScenarioCoverageResponse:
    shift_ids = payload.shift_ids

    # Build assumptions sets
    a = payload.assumptions
    assumptions = Assumptions(
        fix_license_for_provider_ids=set(a.fix_license_for_provider_ids or []),
        fix_acls_for_provider_ids=set(a.fix_acls_for_provider_ids or []),
        assume_payer_for_provider_ids=set(a.assume_payer_for_provider_ids or []),
        assume_privilege_for_provider_ids=set(a.assume_privilege_for_provider_ids or []),
    )

    def _run():
        sql_text, params = shift_recommendations_by_ids_sql(shift_ids)
        rec_rows = databricks.fetch_all(sql_text, params).rows
        recs_by_shift: dict[str, list[str]] = {}
        all_provider_ids: list[str] = []
        for r in rec_rows:
            sid = str(r.get("shift_id"))
            ids = _normalize_recommended_ids(r.get("recommended_provider_ids"))
            recs_by_shift[sid] = ids
            all_provider_ids.extend(ids)

        all_provider_ids = unique_ids(all_provider_ids)
        prov_map = _provider_rows_by_id(all_provider_ids)
        return recs_by_shift, prov_map

    def _mock():
        # Use mock_shift_recommendations per shift (cheap and deterministic)
        recs_by_shift = {}
        all_provider_ids = []
        for sid in shift_ids:
            rec = mock_data.mock_shift_recommendations(sid)
            recs_by_shift[sid] = rec.recommended_provider_ids
            all_provider_ids.extend(rec.recommended_provider_ids)
        all_provider_ids = unique_ids(all_provider_ids)
        prov_map = {p.provider_id: p.model_dump() for p in mock_data.mock_providers() if p.provider_id in set(all_provider_ids)}
        return recs_by_shift, prov_map

    recs_by_shift, prov_map = dbx_or_mock(lambda: databricks.with_retry(_run), _mock)

    results: list[ScenarioShiftResult] = []
    baseline_coverable = 0
    scenario_coverable = 0

    for sid in shift_ids:
        rec_ids = recs_by_shift.get(sid, []) or []

        base_best: Optional[str] = None
        scen_best: Optional[str] = None

        # Baseline decision
        for pid in rec_ids:
            row = prov_map.get(pid)
            if not row:
                continue
            exp = explain_provider_readiness(row, assumptions=Assumptions.empty())
            if exp.is_eligible:
                base_best = pid
                break
        base_ok = base_best is not None

        # Scenario decision
        for pid in rec_ids:
            row = prov_map.get(pid)
            if not row:
                continue
            exp = explain_provider_readiness(row, assumptions=assumptions)
            if exp.is_eligible:
                scen_best = pid
                break
        scen_ok = scen_best is not None

        if base_ok:
            baseline_coverable += 1
        if scen_ok:
            scenario_coverable += 1

        changes = []
        if (not base_ok) and scen_ok:
            changes.append("Scenario made shift coverable via readiness assumptions")

        results.append(
            ScenarioShiftResult(
                shift_id=sid,
                baseline_coverable=base_ok,
                scenario_coverable=scen_ok,
                delta_coverable=(not base_ok) and scen_ok,
                baseline_best_provider_id=base_best,
                scenario_best_provider_id=scen_best,
                scenario_changes=changes,
            )
        )

    return ScenarioCoverageResponse(
        shift_count=len(shift_ids),
        baseline_coverable_count=baseline_coverable,
        scenario_coverable_count=scenario_coverable,
        delta_coverable_count=scenario_coverable - baseline_coverable,
        results=results,
    )

