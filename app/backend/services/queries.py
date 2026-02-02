from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, List, Literal, Optional, Tuple

from settings import settings


def fq_gold(table: str) -> str:
    return f"{settings.databricks_catalog}.{settings.databricks_schema_gold}.{table}"


SortDir = Literal["asc", "desc"]


@dataclass(frozen=True)
class SqlParts:
    where_sql: str
    params: dict[str, Any]


def _csv_list(value: Optional[str]) -> Optional[list[str]]:
    if not value:
        return None
    items = [v.strip() for v in value.split(",") if v.strip()]
    return items or None


def _build_where(clauses: list[str], params: dict[str, Any]) -> SqlParts:
    if not clauses:
        return SqlParts(where_sql="", params=params)
    return SqlParts(where_sql=" WHERE " + " AND ".join(clauses), params=params)


def _safe_sort(sort: Optional[str], allowed_fields: set[str], default: str) -> Tuple[str, SortDir]:
    if not sort:
        return default, "desc"
    # format: field:asc|desc
    parts = sort.split(":")
    field = parts[0].strip()
    direction = (parts[1].strip().lower() if len(parts) > 1 else "desc")
    if field not in allowed_fields:
        return default, "desc"
    if direction not in {"asc", "desc"}:
        direction = "desc"
    return field, direction  # type: ignore[return-value]


def providers_list_sql(
    *,
    q: Optional[str],
    specialty: Optional[str],
    status: Optional[str],
    expiring_within_days: Optional[int],
    page: int,
    page_size: int,
    sort: Optional[str],
) -> Tuple[str, str, dict[str, Any]]:
    table = fq_gold("provider_360_flat")
    clauses: list[str] = []
    params: dict[str, Any] = {}

    if q:
        params["q"] = f"%{q}%"
        clauses.append("(provider_id LIKE :q OR provider_name LIKE :q)")

    if specialty:
        params["specialty"] = specialty
        clauses.append("specialty = :specialty")

    if status:
        params["status"] = status
        clauses.append("provider_status = :status")

    if expiring_within_days is not None:
        params["exp_days"] = int(expiring_within_days)
        clauses.append(
            "("
            "  (state_license_days_left IS NOT NULL AND state_license_days_left <= :exp_days)"
            "  OR (acls_days_left IS NOT NULL AND acls_days_left <= :exp_days)"
            ")"
        )

    where = _build_where(clauses, params)
    allowed = {
        "provider_id",
        "provider_name",
        "specialty",
        "provider_status",
        "home_facility_name",
        "state_license_days_left",
        "acls_days_left",
        "active_privilege_count",
        "active_privilege_facility_count",
        "active_payer_count",
    }
    sort_field, sort_dir = _safe_sort(sort, allowed, default="last_built_at")

    params = {**where.params, "limit": page_size, "offset": (page - 1) * page_size}
    data_sql = (
        f"SELECT * FROM {table}"
        f"{where.where_sql}"
        f" ORDER BY {sort_field} {sort_dir}"
        " LIMIT :limit OFFSET :offset"
    )
    count_sql = f"SELECT COUNT(1) AS total FROM {table}{where.where_sql}"
    return data_sql, count_sql, params


def provider_detail_sql(provider_id: str) -> Tuple[str, dict[str, Any]]:
    table = fq_gold("provider_360_flat")
    return f"SELECT * FROM {table} WHERE provider_id = :provider_id", {"provider_id": provider_id}


def kpi_latest_sql(as_of_date: Optional[date]) -> Tuple[str, dict[str, Any]]:
    table = fq_gold("kpi_summary_daily")
    if as_of_date:
        return (
            f"SELECT * FROM {table} WHERE kpi_date <= :as_of_date ORDER BY kpi_date DESC LIMIT 1",
            {"as_of_date": as_of_date.isoformat()},
        )
    return (f"SELECT * FROM {table} ORDER BY kpi_date DESC LIMIT 1", {})


def staffing_gaps_list_sql(
    *,
    start_date: Optional[date],
    end_date: Optional[date],
    facility_id: Optional[str],
    risk_level: Optional[str],
    procedure_code: Optional[str],
    page: int,
    page_size: int,
    sort: Optional[str],
) -> Tuple[str, str, dict[str, Any]]:
    table = fq_gold("staffing_gaps")
    clauses: list[str] = []
    params: dict[str, Any] = {}

    if start_date:
        params["start_date"] = start_date.isoformat()
        clauses.append("to_date(start_ts) >= :start_date")
    if end_date:
        params["end_date"] = end_date.isoformat()
        clauses.append("to_date(start_ts) <= :end_date")
    if facility_id:
        params["facility_id"] = facility_id
        clauses.append("facility_id = :facility_id")
    if procedure_code:
        params["procedure_code"] = procedure_code
        clauses.append("required_procedure_code = :procedure_code")

    risk_levels = _csv_list(risk_level)
    if risk_levels:
        # named params: risk0, risk1, ...
        placeholders = []
        for i, rl in enumerate(risk_levels):
            key = f"risk{i}"
            params[key] = rl
            placeholders.append(f":{key}")
        clauses.append(f"risk_level IN ({', '.join(placeholders)})")

    where = _build_where(clauses, params)
    allowed = {
        "start_ts",
        "end_ts",
        "facility_name",
        "procedure_name",
        "gap_count",
        "risk_level",
        "eligible_provider_count",
    }
    sort_field, sort_dir = _safe_sort(sort, allowed, default="gap_count")

    params = {**where.params, "limit": page_size, "offset": (page - 1) * page_size}
    data_sql = (
        f"SELECT * FROM {table}"
        f"{where.where_sql}"
        f" ORDER BY {sort_field} {sort_dir}"
        " LIMIT :limit OFFSET :offset"
    )
    count_sql = f"SELECT COUNT(1) AS total FROM {table}{where.where_sql}"
    return data_sql, count_sql, params


def shift_recommendations_sql(shift_id: str) -> Tuple[str, dict[str, Any]]:
    table = fq_gold("shift_recommendations")
    return f"SELECT * FROM {table} WHERE shift_id = :shift_id", {"shift_id": shift_id}


def credential_risk_list_sql(
    *,
    provider_id: Optional[str],
    cred_type: Optional[str],
    risk_bucket: Optional[str],
    page: int,
    page_size: int,
    sort: Optional[str],
) -> Tuple[str, str, dict[str, Any]]:
    table = fq_gold("credential_risk")
    clauses: list[str] = []
    params: dict[str, Any] = {}

    if provider_id:
        params["provider_id"] = provider_id
        clauses.append("provider_id = :provider_id")
    if cred_type:
        params["cred_type"] = cred_type
        clauses.append("cred_type = :cred_type")

    buckets = _csv_list(risk_bucket)
    if buckets:
        placeholders = []
        for i, b in enumerate(buckets):
            key = f"bucket{i}"
            params[key] = b
            placeholders.append(f":{key}")
        clauses.append(f"risk_bucket IN ({', '.join(placeholders)})")

    where = _build_where(clauses, params)
    allowed = {
        "expires_at",
        "days_until_expiration",
        "risk_bucket",
        "cred_type",
        "provider_id",
    }
    sort_field, sort_dir = _safe_sort(sort, allowed, default="days_until_expiration")

    params = {**where.params, "limit": page_size, "offset": (page - 1) * page_size}
    data_sql = (
        f"SELECT * FROM {table}"
        f"{where.where_sql}"
        f" ORDER BY {sort_field} {sort_dir}"
        " LIMIT :limit OFFSET :offset"
    )
    count_sql = f"SELECT COUNT(1) AS total FROM {table}{where.where_sql}"
    return data_sql, count_sql, params


def kpis_trend_sql(days: int) -> Tuple[str, dict[str, Any]]:
    table = fq_gold("kpi_summary_daily")
    sql_text = (
        f"SELECT kpi_date, providers_pending, providers_expiring_30d, daily_revenue_at_risk_est"
        f" FROM {table}"
        f" ORDER BY kpi_date DESC"
        f" LIMIT :days"
    )
    return sql_text, {"days": int(days)}


def staffing_summary_sql(
    *,
    start_date: Optional[date],
    end_date: Optional[date],
    facility_id: Optional[str],
    risk_level: Optional[str],
    procedure_code: Optional[str],
) -> Tuple[dict[str, str], dict[str, Any]]:
    """
    Returns a dict of named queries (by_risk_level, daily_gap_count, top_facilities, top_procedures)
    plus params shared across them.
    """
    table = fq_gold("staffing_gaps")
    clauses: list[str] = []
    params: dict[str, Any] = {}

    if start_date:
        params["start_date"] = start_date.isoformat()
        clauses.append("to_date(start_ts) >= :start_date")
    if end_date:
        params["end_date"] = end_date.isoformat()
        clauses.append("to_date(start_ts) <= :end_date")
    if facility_id:
        params["facility_id"] = facility_id
        clauses.append("facility_id = :facility_id")
    if procedure_code:
        params["procedure_code"] = procedure_code
        clauses.append("required_procedure_code = :procedure_code")
    risk_levels = _csv_list(risk_level)
    if risk_levels:
        placeholders = []
        for i, rl in enumerate(risk_levels):
            key = f"risk{i}"
            params[key] = rl
            placeholders.append(f":{key}")
        clauses.append(f"risk_level IN ({', '.join(placeholders)})")

    where = _build_where(clauses, params).where_sql

    queries = {
        "by_risk_level": f"SELECT risk_level AS label, COUNT(1) AS count FROM {table}{where} GROUP BY risk_level",
        "daily_gap_count": (
            f"SELECT to_date(start_ts) AS date, SUM(gap_count) AS value"
            f" FROM {table}{where} GROUP BY to_date(start_ts) ORDER BY date ASC"
        ),
        "top_facilities": (
            f"SELECT facility_id, facility_name, SUM(gap_count) AS total_gap_count, COUNT(1) AS shift_count"
            f" FROM {table}{where} GROUP BY facility_id, facility_name"
            f" ORDER BY total_gap_count DESC LIMIT 10"
        ),
        "top_procedures": (
            f"SELECT required_procedure_code, procedure_name, SUM(gap_count) AS total_gap_count, COUNT(1) AS shift_count"
            f" FROM {table}{where} GROUP BY required_procedure_code, procedure_name"
            f" ORDER BY total_gap_count DESC LIMIT 10"
        ),
    }
    return queries, params


def credential_risk_summary_sql(
    *,
    cred_type: Optional[str],
    risk_bucket: Optional[str],
) -> Tuple[dict[str, str], dict[str, Any]]:
    table = fq_gold("credential_risk")
    clauses: list[str] = []
    params: dict[str, Any] = {}

    if cred_type:
        params["cred_type"] = cred_type
        clauses.append("cred_type = :cred_type")
    buckets = _csv_list(risk_bucket)
    if buckets:
        placeholders = []
        for i, b in enumerate(buckets):
            key = f"bucket{i}"
            params[key] = b
            placeholders.append(f":{key}")
        clauses.append(f"risk_bucket IN ({', '.join(placeholders)})")

    where = _build_where(clauses, params).where_sql

    queries = {
        "by_bucket": f"SELECT risk_bucket AS label, COUNT(1) AS count FROM {table}{where} GROUP BY risk_bucket",
        "by_cred_type": f"SELECT cred_type AS label, COUNT(1) AS count FROM {table}{where} GROUP BY cred_type",
        "expires_by_week": (
            f"SELECT date_trunc('week', expires_at) AS date, COUNT(1) AS count"
            f" FROM {table}{where} GROUP BY date_trunc('week', expires_at) ORDER BY date ASC"
        ),
    }
    return queries, params


def providers_summary_sql(
    *,
    specialty: Optional[str],
    status: Optional[str],
    expiring_within_days: Optional[int],
) -> Tuple[dict[str, str], dict[str, Any]]:
    table = fq_gold("provider_360_flat")
    clauses: list[str] = []
    params: dict[str, Any] = {}

    if specialty:
        params["specialty"] = specialty
        clauses.append("specialty = :specialty")
    if status:
        params["status"] = status
        clauses.append("provider_status = :status")
    if expiring_within_days is not None:
        params["exp_days"] = int(expiring_within_days)
        clauses.append(
            "("
            "  (state_license_days_left IS NOT NULL AND state_license_days_left <= :exp_days)"
            "  OR (acls_days_left IS NOT NULL AND acls_days_left <= :exp_days)"
            ")"
        )

    where = _build_where(clauses, params).where_sql

    # Readiness score is intentionally simple and explainable.
    readiness_expr = (
        "(CASE WHEN provider_status = 'ACTIVE' THEN 1 ELSE 0 END)"
        " + (CASE WHEN COALESCE(state_license_days_left, -999999) >= 0 THEN 1 ELSE 0 END)"
        " + (CASE WHEN COALESCE(acls_days_left, -999999) >= 0 THEN 1 ELSE 0 END)"
        " + (CASE WHEN COALESCE(active_payer_count, 0) > 0 THEN 1 ELSE 0 END)"
        " + (CASE WHEN COALESCE(active_privilege_count, 0) > 0 THEN 1 ELSE 0 END)"
    )

    queries = {
        "by_specialty": f"SELECT specialty AS label, COUNT(1) AS count FROM {table}{where} GROUP BY specialty ORDER BY count DESC LIMIT 12",
        "expiring_funnel": (
            f"""
SELECT label, count FROM (
  SELECT '<=14' AS label,
         SUM(CASE WHEN LEAST(COALESCE(state_license_days_left, 999999), COALESCE(acls_days_left, 999999)) <= 14 THEN 1 ELSE 0 END) AS count
  FROM {table}{where}
  UNION ALL
  SELECT '<=30' AS label,
         SUM(CASE WHEN LEAST(COALESCE(state_license_days_left, 999999), COALESCE(acls_days_left, 999999)) <= 30 THEN 1 ELSE 0 END) AS count
  FROM {table}{where}
  UNION ALL
  SELECT '<=90' AS label,
         SUM(CASE WHEN LEAST(COALESCE(state_license_days_left, 999999), COALESCE(acls_days_left, 999999)) <= 90 THEN 1 ELSE 0 END) AS count
  FROM {table}{where}
)
"""
        ),
        "readiness_histogram": (
            f"""
SELECT label, count
FROM (
  SELECT CAST({readiness_expr} AS INT) AS score,
         CAST({readiness_expr} AS STRING) AS label,
         COUNT(1) AS count
  FROM {table}{where}
  GROUP BY CAST({readiness_expr} AS INT), CAST({readiness_expr} AS STRING)
)
ORDER BY score ASC
"""
        ),
    }
    return queries, params


def shift_prediction_sql(shift_id: str) -> Tuple[str, dict[str, Any]]:
    table = fq_gold("shift_gap_predictions")
    return (
        f"""
SELECT shift_id, predicted_gap_prob, predicted_is_gap, scored_at
FROM {table}
WHERE shift_id = :shift_id
ORDER BY scored_at DESC
LIMIT 1
""",
        {"shift_id": shift_id},
    )


def actions_list_sql(
    *,
    entity_type: Optional[str],
    entity_id: Optional[str],
    status: Optional[str],
    action_type: Optional[str],
    facility_id: Optional[str],
    page: int,
    page_size: int,
    sort: Optional[str],
) -> Tuple[str, str, dict[str, Any]]:
    table = fq_gold("risk_actions")
    clauses: list[str] = []
    params: dict[str, Any] = {}

    if entity_type:
        params["entity_type"] = entity_type
        clauses.append("entity_type = :entity_type")
    if entity_id:
        params["entity_id"] = entity_id
        clauses.append("entity_id = :entity_id")
    if status:
        params["status"] = status
        clauses.append("status = :status")
    if action_type:
        params["action_type"] = action_type
        clauses.append("action_type = :action_type")
    if facility_id:
        params["facility_id"] = facility_id
        clauses.append("facility_id = :facility_id")

    where = _build_where(clauses, params)
    allowed = {
        "created_at",
        "updated_at",
        "resolved_at",
        "priority",
        "status",
        "action_type",
    }
    sort_field, sort_dir = _safe_sort(sort, allowed, default="created_at")

    params = {**where.params, "limit": page_size, "offset": (page - 1) * page_size}
    data_sql = (
        f"SELECT * FROM {table}"
        f"{where.where_sql}"
        f" ORDER BY {sort_field} {sort_dir}"
        " LIMIT :limit OFFSET :offset"
    )
    count_sql = f"SELECT COUNT(1) AS total FROM {table}{where.where_sql}"
    return data_sql, count_sql, params


def action_by_id_sql(action_id: str) -> Tuple[str, dict[str, Any]]:
    table = fq_gold("risk_actions")
    return f"SELECT * FROM {table} WHERE action_id = :action_id", {"action_id": action_id}


