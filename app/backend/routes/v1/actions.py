from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Body, HTTPException, Path, Query

from models.actions import ActionsSummary, CreateRiskActionRequest, RiskAction, UpdateRiskActionRequest
from models.common import PageResponse
from services import databricks, mock_data
from services.databricks import DatabricksNotConfigured
from services.queries import action_by_id_sql, actions_list_sql
from settings import settings

router = APIRouter()


def _now() -> datetime:
    return datetime.now(timezone.utc)

 
def _looks_like_missing_table(exc: Exception) -> bool:
    msg = str(exc).lower()
    return ("not found" in msg and "risk_actions" in msg) or ("table or view not found" in msg) or ("table_or_view_not_found" in msg)


@router.get("/actions", response_model=PageResponse[RiskAction])
def list_actions(
    entity_type: Optional[str] = Query(default=None, description="SHIFT|PROVIDER"),
    entity_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None, description="OPEN|IN_PROGRESS|RESOLVED"),
    action_type: Optional[str] = Query(default=None),
    facility_id: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    sort: Optional[str] = Query(default=None, description="field:asc|desc"),
) -> PageResponse[RiskAction]:
    data_sql, count_sql, params = actions_list_sql(
        entity_type=entity_type,
        entity_id=entity_id,
        status=status,
        action_type=action_type,
        facility_id=facility_id,
        page=page,
        page_size=page_size,
        sort=sort,
    )

    def _run():
        items, total = databricks.fetch_paged(data_sql, count_sql, params)
        return items, total

    try:
        items, total = databricks.with_retry(_run)
        parsed = [RiskAction.model_validate(r) for r in items]
        return PageResponse[RiskAction](items=parsed, total=total, page=page, page_size=page_size)
    except DatabricksNotConfigured:
        if not settings.use_mock_data:
            raise HTTPException(status_code=503, detail="Databricks not configured (no warehouse/token).")
        return mock_data.mock_actions_page(
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
            action_type=action_type,
            facility_id=facility_id,
            page=page,
            page_size=page_size,
        )
    except Exception as e:  # noqa: BLE001
        if _looks_like_missing_table(e):
            raise HTTPException(status_code=503, detail="Missing table: gold.risk_actions. Run notebook 04_build_gold_views.ipynb to create it.")
        raise


@router.get("/actions/summary", response_model=ActionsSummary)
def actions_summary(
    facility_id: Optional[str] = Query(default=None),
) -> ActionsSummary:
    # Minimal summary is computed in-app to avoid adding extra DB aggregation endpoints.
    try:
        page = list_actions(facility_id=facility_id, page=1, page_size=500, sort="updated_at:desc")
        items = page.items
    except Exception:
        # For any unexpected errors, fall back to a safe mock summary.
        items = mock_data.mock_actions_page(facility_id=facility_id, page=1, page_size=500).items

    open_count = sum(1 for a in items if a.status == "OPEN")
    in_prog = sum(1 for a in items if a.status == "IN_PROGRESS")
    resolved = sum(1 for a in items if a.status == "RESOLVED")

    # Median time-to-resolve (hours) for resolved actions (best-effort)
    durations = []
    for a in items:
        if a.status == "RESOLVED" and a.resolved_at:
            durations.append((a.resolved_at - a.created_at).total_seconds() / 3600.0)
    durations.sort()
    median = None
    if durations:
        mid = len(durations) // 2
        median = durations[mid] if (len(durations) % 2 == 1) else (durations[mid - 1] + durations[mid]) / 2.0

    return ActionsSummary(
        open_count=open_count,
        in_progress_count=in_prog,
        resolved_count=resolved,
        median_time_to_resolve_hours=median,
    )


@router.post("/actions", response_model=RiskAction)
def create_action(payload: CreateRiskActionRequest = Body(...)) -> RiskAction:
    action_id = str(uuid4())
    now = _now()

    insert_sql = f"""
INSERT INTO {databricks_sql_table()}
(
  action_id, entity_type, entity_id, facility_id,
  action_type, status, priority, owner,
  created_at, updated_at, resolved_at,
  notes, last_built_at
)
VALUES
(
  :action_id, :entity_type, :entity_id, :facility_id,
  :action_type, :status, :priority, :owner,
  :created_at, :updated_at, :resolved_at,
  :notes, :last_built_at
)
"""

    params = {
        "action_id": action_id,
        "entity_type": payload.entity_type,
        "entity_id": payload.entity_id,
        "facility_id": payload.facility_id,
        "action_type": payload.action_type,
        "status": "OPEN",
        "priority": payload.priority,
        "owner": payload.owner,
        "created_at": now,
        "updated_at": now,
        "resolved_at": None,
        "notes": payload.notes,
        "last_built_at": now,
    }

    try:
        databricks.execute(insert_sql, params)
        sel_sql, sel_params = action_by_id_sql(action_id)
        row = databricks.fetch_all(sel_sql, sel_params).rows[0]
        return RiskAction.model_validate(row)
    except DatabricksNotConfigured:
        if not settings.use_mock_data:
            raise HTTPException(status_code=503, detail="Databricks not configured (no warehouse/token).")
        return mock_data.mock_actions_create(payload)
    except Exception as e:  # noqa: BLE001
        if _looks_like_missing_table(e):
            raise HTTPException(status_code=503, detail="Missing table: gold.risk_actions. Run notebook 04_build_gold_views.ipynb to create it.")
        raise


@router.patch("/actions/{action_id}", response_model=RiskAction)
def update_action(
    action_id: str = Path(...),
    payload: UpdateRiskActionRequest = Body(...),
) -> RiskAction:
    try:
        return _update_action_db(action_id, payload)
    except DatabricksNotConfigured:
        return mock_data.mock_actions_update(action_id, payload)
    except Exception as e:  # noqa: BLE001
        if _looks_like_missing_table(e):
            raise HTTPException(status_code=503, detail="Missing table: gold.risk_actions. Run notebook 04_build_gold_views.ipynb to create it.")
        raise


def databricks_sql_table() -> str:
    # Local helper avoids importing queries module for DML string formatting.
    from settings import settings

    return f"{settings.databricks_catalog}.{settings.databricks_schema_gold}.risk_actions"


def _update_action_db(action_id: str, payload: UpdateRiskActionRequest) -> RiskAction:
    table = databricks_sql_table()
    sets = ["updated_at = current_timestamp()", "last_built_at = current_timestamp()"]
    params: dict[str, object] = {"action_id": action_id}

    if payload.status is not None:
        params["status"] = payload.status
        sets.append("status = :status")
        # Keep resolved_at in sync with status (server timestamp)
        sets.append("resolved_at = CASE WHEN :status = 'RESOLVED' THEN current_timestamp() ELSE NULL END")

    if payload.priority is not None:
        params["priority"] = payload.priority
        sets.append("priority = :priority")

    if payload.owner is not None:
        params["owner"] = payload.owner
        sets.append("owner = :owner")

    if payload.notes is not None:
        params["notes"] = payload.notes
        sets.append("notes = :notes")

    if len(sets) <= 2:
        # nothing to update besides timestamps
        sel_sql, sel_params = action_by_id_sql(action_id)
        rows = databricks.fetch_all(sel_sql, sel_params).rows
        if not rows:
            raise ValueError("Action not found")
        return RiskAction.model_validate(rows[0])

    sql_text = f"UPDATE {table} SET " + ", ".join(sets) + " WHERE action_id = :action_id"
    databricks.execute(sql_text, params)

    sel_sql, sel_params = action_by_id_sql(action_id)
    rows = databricks.fetch_all(sel_sql, sel_params).rows
    if not rows:
        raise ValueError("Action not found")
    return RiskAction.model_validate(rows[0])

