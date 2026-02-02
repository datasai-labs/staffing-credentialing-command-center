from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Literal, Optional, Tuple

from settings import settings

SortDir = Literal["asc", "desc"]

def fq_gold(table: str) -> str:
    return f"{settings.databricks_catalog}.{settings.databricks_schema_gold}.{table}"

def fq_ref(table: str) -> str:
    return f"{settings.databricks_catalog}.{settings.databricks_schema_ref}.{table}"

def fq_silver(table: str) -> str:
    return f"{settings.databricks_catalog}.{settings.databricks_schema_silver}.{table}"


@dataclass(frozen=True)
class SqlParts:
    where_sql: str
    params: dict[str, Any]


class QueryBuilder:
    """Fluent SQL query builder for common patterns."""
    
    def __init__(self, table: str):
        self.table = table
        self.clauses: list[str] = []
        self.params: dict[str, Any] = {}
    
    def eq(self, col: str, value: Any, param: Optional[str] = None) -> "QueryBuilder":
        if value is not None:
            p = param or col
            self.params[p] = value
            self.clauses.append(f"{col} = :{p}")
        return self
    
    def like(self, col: str, value: Optional[str], param: str) -> "QueryBuilder":
        if value:
            self.params[param] = f"%{value}%"
            self.clauses.append(f"{col} LIKE :{param}")
        return self
    
    def gte(self, col: str, value: Any, param: str) -> "QueryBuilder":
        if value is not None:
            self.params[param] = value.isoformat() if hasattr(value, 'isoformat') else value
            self.clauses.append(f"{col} >= :{param}")
        return self
    
    def lte(self, col: str, value: Any, param: str) -> "QueryBuilder":
        if value is not None:
            self.params[param] = value.isoformat() if hasattr(value, 'isoformat') else value
            self.clauses.append(f"{col} <= :{param}")
        return self
    
    def in_list(self, col: str, csv_value: Optional[str], prefix: str) -> "QueryBuilder":
        if not csv_value:
            return self
        items = [v.strip() for v in csv_value.split(",") if v.strip()]
        if items:
            placeholders = []
            for i, item in enumerate(items):
                key = f"{prefix}{i}"
                self.params[key] = item
                placeholders.append(f":{key}")
            self.clauses.append(f"{col} IN ({', '.join(placeholders)})")
        return self
    
    def raw(self, clause: str) -> "QueryBuilder":
        self.clauses.append(clause)
        return self
    
    def where_sql(self) -> str:
        return " WHERE " + " AND ".join(self.clauses) if self.clauses else ""
    
    def paged_sql(self, sort_field: str, sort_dir: SortDir, page: int, page_size: int) -> Tuple[str, str, dict[str, Any]]:
        where = self.where_sql()
        params = {**self.params, "limit": page_size, "offset": (page - 1) * page_size}
        data_sql = f"SELECT * FROM {self.table}{where} ORDER BY {sort_field} {sort_dir} LIMIT :limit OFFSET :offset"
        count_sql = f"SELECT COUNT(1) AS total FROM {self.table}{where}"
        return data_sql, count_sql, params


def _safe_sort(sort: Optional[str], allowed: set[str], default: str) -> Tuple[str, SortDir]:
    if not sort:
        return default, "desc"
    parts = sort.split(":")
    field = parts[0].strip()
    direction = parts[1].strip().lower() if len(parts) > 1 else "desc"
    if field not in allowed:
        return default, "desc"
    return field, direction if direction in {"asc", "desc"} else "desc"  # type: ignore


def _in_clause(ids: list[str], prefix: str) -> Tuple[str, dict[str, Any]]:
    if not ids:
        return "1=0", {}
    placeholders = ", ".join([f":{prefix}{i}" for i in range(len(ids))])
    params = {f"{prefix}{i}": sid for i, sid in enumerate(ids)}
    return f"IN ({placeholders})", params


# ─────────────────────────────────────────────────────────────────────────────
# Provider queries
# ─────────────────────────────────────────────────────────────────────────────

def providers_list_sql(*, q: Optional[str], specialty: Optional[str], status: Optional[str],
                       expiring_within_days: Optional[int], page: int, page_size: int, sort: Optional[str]
) -> Tuple[str, str, dict[str, Any]]:
    qb = QueryBuilder(fq_gold("provider_360_flat"))
    if q:
        qb.params["q"] = f"%{q}%"
        qb.raw("(provider_id LIKE :q OR provider_name LIKE :q)")
    qb.eq("specialty", specialty).eq("provider_status", status, "status")
    if expiring_within_days is not None:
        qb.params["exp_days"] = expiring_within_days
        qb.raw("((state_license_days_left IS NOT NULL AND state_license_days_left <= :exp_days) "
               "OR (acls_days_left IS NOT NULL AND acls_days_left <= :exp_days))")
    
    allowed = {"provider_id", "provider_name", "specialty", "provider_status", "home_facility_name",
               "state_license_days_left", "acls_days_left", "active_privilege_count", "active_privilege_facility_count", "active_payer_count"}
    sort_field, sort_dir = _safe_sort(sort, allowed, "last_built_at")
    return qb.paged_sql(sort_field, sort_dir, page, page_size)


def provider_detail_sql(provider_id: str) -> Tuple[str, dict[str, Any]]:
    return f"SELECT * FROM {fq_gold('provider_360_flat')} WHERE provider_id = :provider_id", {"provider_id": provider_id}


def providers_blockers_worklist_sql(*, facility_id: Optional[str], specialty: Optional[str], blocker: Optional[str],
                                    page: int, page_size: int, sort: Optional[str]) -> Tuple[str, str, dict[str, Any]]:
    qb = QueryBuilder(fq_gold("provider_360_flat"))
    qb.raw("provider_status = 'ACTIVE'")
    qb.eq("home_facility_id", facility_id, "facility_id").eq("specialty", specialty)
    
    blocker_map = {"LICENSE": "COALESCE(state_license_days_left, -999999) < 0",
                   "ACLS": "COALESCE(acls_days_left, -999999) < 0",
                   "PRIVILEGE": "COALESCE(active_privilege_count, 0) = 0",
                   "PAYER": "COALESCE(active_payer_count, 0) = 0"}
    if blocker and blocker.upper() in blocker_map:
        qb.raw(blocker_map[blocker.upper()])
    
    qb.raw("(COALESCE(state_license_days_left, -999999) < 0 OR COALESCE(acls_days_left, -999999) < 0 "
           "OR COALESCE(active_privilege_count, 0) = 0 OR COALESCE(active_payer_count, 0) = 0)")
    
    allowed = {"provider_name", "specialty", "home_facility_name", "state_license_days_left",
               "acls_days_left", "active_privilege_count", "active_payer_count", "last_built_at"}
    sort_field, sort_dir = _safe_sort(sort, allowed, "last_built_at")
    return qb.paged_sql(sort_field, sort_dir, page, page_size)


# ─────────────────────────────────────────────────────────────────────────────
# KPI queries
# ─────────────────────────────────────────────────────────────────────────────

def kpi_latest_sql(as_of_date: Optional[date]) -> Tuple[str, dict[str, Any]]:
    table = fq_gold("kpi_summary_daily")
    if as_of_date:
        return f"SELECT * FROM {table} WHERE kpi_date <= :as_of_date ORDER BY kpi_date DESC LIMIT 1", {"as_of_date": as_of_date.isoformat()}
    return f"SELECT * FROM {table} ORDER BY kpi_date DESC LIMIT 1", {}


def kpis_trend_sql(days: int) -> Tuple[str, dict[str, Any]]:
    return (f"SELECT kpi_date, providers_pending, providers_expiring_30d, daily_revenue_at_risk_est "
            f"FROM {fq_gold('kpi_summary_daily')} ORDER BY kpi_date DESC LIMIT :days", {"days": days})


# ─────────────────────────────────────────────────────────────────────────────
# Staffing gap queries
# ─────────────────────────────────────────────────────────────────────────────

def _staffing_gaps_builder(start_date: Optional[date], end_date: Optional[date], facility_id: Optional[str],
                           risk_level: Optional[str], procedure_code: Optional[str]) -> QueryBuilder:
    qb = QueryBuilder(fq_gold("staffing_gaps"))
    qb.gte("to_date(start_ts)", start_date, "start_date")
    qb.lte("to_date(start_ts)", end_date, "end_date")
    qb.eq("facility_id", facility_id).eq("required_procedure_code", procedure_code, "procedure_code")
    qb.in_list("risk_level", risk_level, "risk")
    return qb


def staffing_gaps_list_sql(*, start_date: Optional[date], end_date: Optional[date], facility_id: Optional[str],
                           risk_level: Optional[str], procedure_code: Optional[str], page: int, page_size: int, sort: Optional[str]
) -> Tuple[str, str, dict[str, Any]]:
    qb = _staffing_gaps_builder(start_date, end_date, facility_id, risk_level, procedure_code)
    allowed = {"start_ts", "end_ts", "facility_name", "procedure_name", "gap_count", "risk_level", "eligible_provider_count"}
    sort_field, sort_dir = _safe_sort(sort, allowed, "gap_count")
    return qb.paged_sql(sort_field, sort_dir, page, page_size)


def staffing_gaps_no_eligible_list_sql(*, start_date: Optional[date], end_date: Optional[date], facility_id: Optional[str],
                                       risk_level: Optional[str], procedure_code: Optional[str], page: int, page_size: int, sort: Optional[str]
) -> Tuple[str, str, dict[str, Any]]:
    data_sql, count_sql, params = staffing_gaps_list_sql(
        start_date=start_date, end_date=end_date, facility_id=facility_id,
        risk_level=risk_level, procedure_code=procedure_code, page=page, page_size=page_size, sort=sort)
    inject = " WHERE eligible_provider_count = 0 AND " if " WHERE " in data_sql else " WHERE eligible_provider_count = 0"
    data_sql = data_sql.replace(" WHERE ", inject, 1) if " WHERE " in data_sql else data_sql.replace(" ORDER BY", f"{inject} ORDER BY")
    count_sql = count_sql.replace(" WHERE ", inject, 1) if " WHERE " in count_sql else count_sql + inject.rstrip(" AND ")
    return data_sql, count_sql, params


def staffing_gaps_by_ids_sql(shift_ids: list[str]) -> Tuple[str, dict[str, Any]]:
    in_clause, params = _in_clause(shift_ids, "sid")
    return f"SELECT * FROM {fq_gold('staffing_gaps')} WHERE shift_id {in_clause}", params


def shift_recommendations_sql(shift_id: str) -> Tuple[str, dict[str, Any]]:
    return f"SELECT * FROM {fq_gold('shift_recommendations')} WHERE shift_id = :shift_id", {"shift_id": shift_id}


def shift_recommendations_by_ids_sql(shift_ids: list[str]) -> Tuple[str, dict[str, Any]]:
    in_clause, params = _in_clause(shift_ids, "sid")
    return f"SELECT * FROM {fq_gold('shift_recommendations')} WHERE shift_id {in_clause}", params


def shift_prediction_sql(shift_id: str) -> Tuple[str, dict[str, Any]]:
    return (f"SELECT shift_id, predicted_gap_prob, predicted_is_gap, scored_at FROM {fq_gold('shift_gap_predictions')} "
            f"WHERE shift_id = :shift_id ORDER BY scored_at DESC LIMIT 1", {"shift_id": shift_id})


# ─────────────────────────────────────────────────────────────────────────────
# Credential risk queries
# ─────────────────────────────────────────────────────────────────────────────

def credential_risk_list_sql(*, provider_id: Optional[str], cred_type: Optional[str], risk_bucket: Optional[str],
                             page: int, page_size: int, sort: Optional[str]) -> Tuple[str, str, dict[str, Any]]:
    qb = QueryBuilder(fq_gold("credential_risk"))
    qb.eq("provider_id", provider_id).eq("cred_type", cred_type).in_list("risk_bucket", risk_bucket, "bucket")
    allowed = {"expires_at", "days_until_expiration", "risk_bucket", "cred_type", "provider_id"}
    sort_field, sort_dir = _safe_sort(sort, allowed, "days_until_expiration")
    return qb.paged_sql(sort_field, sort_dir, page, page_size)


def credential_expiring_worklist_sql(*, provider_id: Optional[str], specialty: Optional[str], facility_id: Optional[str],
                                     cred_type: Optional[str], risk_bucket: Optional[str], page: int, page_size: int, sort: Optional[str]
) -> Tuple[str, str, dict[str, Any]]:
    cr, p = fq_gold("credential_risk"), fq_gold("provider_360_flat")
    qb = QueryBuilder(f"{cr} cr LEFT JOIN {p} p ON p.provider_id = cr.provider_id")
    qb.eq("cr.provider_id", provider_id, "provider_id").eq("cr.cred_type", cred_type, "cred_type")
    qb.eq("p.specialty", specialty, "specialty").eq("p.home_facility_id", facility_id, "facility_id")
    qb.in_list("cr.risk_bucket", risk_bucket, "bucket")
    
    allowed = {"expires_at", "days_until_expiration", "risk_bucket", "cred_type", "provider_id", "provider_name", "specialty", "home_facility_name"}
    sort_field, sort_dir = _safe_sort(sort, allowed, "days_until_expiration")
    where = qb.where_sql()
    params = {**qb.params, "limit": page_size, "offset": (page - 1) * page_size}
    
    select = f"SELECT cr.*, p.provider_name, p.specialty, p.home_facility_id, p.home_facility_name FROM {cr} cr LEFT JOIN {p} p ON p.provider_id = cr.provider_id"
    data_sql = f"{select}{where} ORDER BY {sort_field} {sort_dir} LIMIT :limit OFFSET :offset"
    count_sql = f"SELECT COUNT(1) AS total FROM {cr} cr LEFT JOIN {p} p ON p.provider_id = cr.provider_id{where}"
    return data_sql, count_sql, params


# ─────────────────────────────────────────────────────────────────────────────
# Actions queries
# ─────────────────────────────────────────────────────────────────────────────

def actions_list_sql(*, entity_type: Optional[str], entity_id: Optional[str], status: Optional[str],
                     action_type: Optional[str], facility_id: Optional[str], page: int, page_size: int, sort: Optional[str]
) -> Tuple[str, str, dict[str, Any]]:
    qb = QueryBuilder(fq_gold("risk_actions"))
    qb.eq("entity_type", entity_type).eq("entity_id", entity_id).eq("status", status)
    qb.eq("action_type", action_type).eq("facility_id", facility_id)
    allowed = {"created_at", "updated_at", "resolved_at", "priority", "status", "action_type"}
    sort_field, sort_dir = _safe_sort(sort, allowed, "created_at")
    return qb.paged_sql(sort_field, sort_dir, page, page_size)


def action_by_id_sql(action_id: str) -> Tuple[str, dict[str, Any]]:
    return f"SELECT * FROM {fq_gold('risk_actions')} WHERE action_id = :action_id", {"action_id": action_id}


# ─────────────────────────────────────────────────────────────────────────────
# Summary/analytics queries
# ─────────────────────────────────────────────────────────────────────────────

def staffing_summary_sql(*, start_date: Optional[date], end_date: Optional[date], facility_id: Optional[str],
                         risk_level: Optional[str], procedure_code: Optional[str]) -> Tuple[dict[str, str], dict[str, Any]]:
    qb = _staffing_gaps_builder(start_date, end_date, facility_id, risk_level, procedure_code)
    table, where = fq_gold("staffing_gaps"), qb.where_sql()
    return {
        "by_risk_level": f"SELECT risk_level AS label, COUNT(1) AS count FROM {table}{where} GROUP BY risk_level",
        "daily_gap_count": f"SELECT to_date(start_ts) AS date, SUM(gap_count) AS value FROM {table}{where} GROUP BY to_date(start_ts) ORDER BY date ASC",
        "top_facilities": f"SELECT facility_id, facility_name, SUM(gap_count) AS total_gap_count, COUNT(1) AS shift_count FROM {table}{where} GROUP BY facility_id, facility_name ORDER BY total_gap_count DESC LIMIT 10",
        "top_procedures": f"SELECT required_procedure_code, procedure_name, SUM(gap_count) AS total_gap_count, COUNT(1) AS shift_count FROM {table}{where} GROUP BY required_procedure_code, procedure_name ORDER BY total_gap_count DESC LIMIT 10",
    }, qb.params


def credential_risk_summary_sql(*, cred_type: Optional[str], risk_bucket: Optional[str]) -> Tuple[dict[str, str], dict[str, Any]]:
    qb = QueryBuilder(fq_gold("credential_risk"))
    qb.eq("cred_type", cred_type).in_list("risk_bucket", risk_bucket, "bucket")
    table, where = fq_gold("credential_risk"), qb.where_sql()
    return {
        "by_bucket": f"SELECT risk_bucket AS label, COUNT(1) AS count FROM {table}{where} GROUP BY risk_bucket",
        "by_cred_type": f"SELECT cred_type AS label, COUNT(1) AS count FROM {table}{where} GROUP BY cred_type",
        "expires_by_week": f"SELECT date_trunc('week', expires_at) AS date, COUNT(1) AS count FROM {table}{where} GROUP BY date_trunc('week', expires_at) ORDER BY date ASC",
    }, qb.params


def providers_summary_sql(*, specialty: Optional[str], status: Optional[str], expiring_within_days: Optional[int]
) -> Tuple[dict[str, str], dict[str, Any]]:
    table = fq_gold("provider_360_flat")
    qb = QueryBuilder(table)
    qb.eq("specialty", specialty).eq("provider_status", status, "status")
    if expiring_within_days is not None:
        qb.params["exp_days"] = expiring_within_days
        qb.raw("((state_license_days_left IS NOT NULL AND state_license_days_left <= :exp_days) "
               "OR (acls_days_left IS NOT NULL AND acls_days_left <= :exp_days))")
    where = qb.where_sql()
    
    readiness = ("(CASE WHEN provider_status = 'ACTIVE' THEN 1 ELSE 0 END) + "
                 "(CASE WHEN COALESCE(state_license_days_left, -999999) >= 0 THEN 1 ELSE 0 END) + "
                 "(CASE WHEN COALESCE(acls_days_left, -999999) >= 0 THEN 1 ELSE 0 END) + "
                 "(CASE WHEN COALESCE(active_payer_count, 0) > 0 THEN 1 ELSE 0 END) + "
                 "(CASE WHEN COALESCE(active_privilege_count, 0) > 0 THEN 1 ELSE 0 END)")
    
    return {
        "by_specialty": f"SELECT specialty AS label, COUNT(1) AS count FROM {table}{where} GROUP BY specialty ORDER BY count DESC LIMIT 12",
        "expiring_funnel": f"""SELECT label, count FROM (
            SELECT '<=14' AS label, SUM(CASE WHEN LEAST(COALESCE(state_license_days_left, 999999), COALESCE(acls_days_left, 999999)) <= 14 THEN 1 ELSE 0 END) AS count FROM {table}{where}
            UNION ALL SELECT '<=30' AS label, SUM(CASE WHEN LEAST(COALESCE(state_license_days_left, 999999), COALESCE(acls_days_left, 999999)) <= 30 THEN 1 ELSE 0 END) AS count FROM {table}{where}
            UNION ALL SELECT '<=90' AS label, SUM(CASE WHEN LEAST(COALESCE(state_license_days_left, 999999), COALESCE(acls_days_left, 999999)) <= 90 THEN 1 ELSE 0 END) AS count FROM {table}{where})""",
        "readiness_histogram": f"SELECT CAST({readiness} AS STRING) AS label, COUNT(1) AS count FROM {table}{where} GROUP BY CAST({readiness} AS INT), CAST({readiness} AS STRING) ORDER BY CAST({readiness} AS INT) ASC",
    }, qb.params
