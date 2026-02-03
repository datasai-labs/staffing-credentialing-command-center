from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from models.common import PageResponse, parse_date
from models.nurse_staffing import (
    CensusForecast,
    CostBreakdown,
    CredentialGapRow,
    NurseStaffingKpis,
    NurseStaffingSummary,
    OptimizationSummary,
    StaffingOptimization,
    UnitDetail,
)
from routes.v1._dbx import dbx_or_mock
from services import databricks, mock_data
from services.queries import fq_gold, fq_ref, fq_silver

router = APIRouter(prefix="/nurse_staffing")


@router.get("/kpis", response_model=NurseStaffingKpis)
def get_nurse_staffing_kpis(
    facility_id: Optional[str] = None,
    kpi_date: Optional[str] = Query(default=None, description="YYYY-MM-DD, defaults to today"),
):
    """Get KPI tiles for the nurse staffing dashboard."""
    target_date = parse_date(kpi_date) if kpi_date else date.today()

    def _run():
        # Query aggregated data from gold.nurse_staffing_summary
        # Use the most recent summary_date available (the table might have been built on a different day)
        facility_filter = f"AND facility_id = :fac" if facility_id else ""
        sql = f"""
            SELECT
                MAX(summary_date) as kpi_date,
                COALESCE(SUM(nurses_assigned), 0) as total_nurses_on_shift,
                SUM(CASE WHEN staffing_status = 'UNDERSTAFFED' THEN 1 ELSE 0 END) as units_understaffed,
                SUM(CASE WHEN staffing_status = 'OPTIMAL' THEN 1 ELSE 0 END) as units_optimal,
                SUM(CASE WHEN staffing_status = 'OVERSTAFFED' THEN 1 ELSE 0 END) as units_overstaffed,
                COALESCE(100.0 * SUM(nurses_contract + nurses_agency) / NULLIF(SUM(nurses_assigned), 0), 0) as agency_contract_percentage,
                COALESCE(SUM(labor_cost_daily), 0) as daily_labor_cost,
                0 as credential_gaps_count,
                current_timestamp() as last_built_at
            FROM {fq_gold('nurse_staffing_summary')}
            WHERE 1=1 {facility_filter}
        """
        params = {}
        if facility_id:
            params["fac"] = facility_id
        rows = databricks.fetch_all(sql, params).rows
        return rows[0] if rows else None

    def _mock():
        return mock_data.mock_nurse_staffing_kpis(facility_id=facility_id)

    row = dbx_or_mock(_run, _mock)
    if isinstance(row, NurseStaffingKpis):
        return row
    return NurseStaffingKpis.model_validate(row)


@router.get("/summary", response_model=PageResponse[NurseStaffingSummary])
def list_nurse_staffing_summary(
    facility_id: Optional[str] = None,
    unit_type: Optional[str] = Query(default=None, description="Comma-separated unit types: ICU,MED_SURG,etc"),
    staffing_status: Optional[str] = Query(default=None, description="Comma-separated: UNDERSTAFFED,OPTIMAL,OVERSTAFFED"),
    summary_date: Optional[str] = Query(default=None, description="YYYY-MM-DD, defaults to today"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
):
    """List staffing summary by unit with filters."""
    target_date = parse_date(summary_date) if summary_date else date.today()

    def _run():
        # Don't filter by date - get all available data (the table contains latest snapshot)
        filters = []
        params = {}

        if facility_id:
            filters.append("facility_id = :fac")
            params["fac"] = facility_id

        if unit_type:
            unit_types = [t.strip() for t in unit_type.split(",") if t.strip()]
            placeholders = ", ".join([f":ut{i}" for i in range(len(unit_types))])
            filters.append(f"unit_type IN ({placeholders})")
            for i, ut in enumerate(unit_types):
                params[f"ut{i}"] = ut

        if staffing_status:
            statuses = [s.strip() for s in staffing_status.split(",") if s.strip()]
            placeholders = ", ".join([f":ss{i}" for i in range(len(statuses))])
            filters.append(f"staffing_status IN ({placeholders})")
            for i, ss in enumerate(statuses):
                params[f"ss{i}"] = ss

        where_clause = " AND ".join(filters) if filters else "1=1"
        offset = (page - 1) * page_size
        params["limit"] = page_size
        params["offset"] = offset

        data_sql = f"""
            SELECT * FROM {fq_gold('nurse_staffing_summary')}
            WHERE {where_clause}
            ORDER BY staffing_status DESC, unit_name
            LIMIT :limit OFFSET :offset
        """
        count_sql = f"""
            SELECT COUNT(*) as cnt FROM {fq_gold('nurse_staffing_summary')}
            WHERE {where_clause}
        """
        return databricks.fetch_paged(data_sql, count_sql, params)

    def _mock():
        all_items = mock_data.mock_nurse_staffing_summary()
        items = all_items
        if facility_id:
            items = [r for r in items if r.facility_id == facility_id]
        if unit_type:
            allowed = {t.strip() for t in unit_type.split(",") if t.strip()}
            items = [r for r in items if r.unit_type in allowed]
        if staffing_status:
            allowed = {s.strip() for s in staffing_status.split(",") if s.strip()}
            items = [r for r in items if r.staffing_status in allowed]
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return (items[start:end], total)

    rows, total = dbx_or_mock(lambda: databricks.with_retry(_run), _mock)
    items = [NurseStaffingSummary.model_validate(r) if not isinstance(r, NurseStaffingSummary) else r for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/units/{unit_id}", response_model=UnitDetail)
def get_unit_detail(unit_id: str):
    """Get detailed view of a single unit with assigned nurses."""

    def _run():
        # Fetch unit info
        unit_sql = f"""
            SELECT u.unit_id, u.facility_id, f.facility_name, u.unit_name, u.unit_type, u.bed_count, u.target_ratio
            FROM {fq_ref('unit')} u
            LEFT JOIN {fq_ref('facility')} f ON u.facility_id = f.facility_id
            WHERE u.unit_id = :uid
        """
        unit_rows = databricks.fetch_all(unit_sql, {"uid": unit_id}).rows
        if not unit_rows:
            return None
        unit_row = unit_rows[0]
        
        # Fetch summary info (use latest available date)
        summary_sql = f"""
            SELECT * FROM {fq_gold('nurse_staffing_summary')}
            WHERE unit_id = :uid
            ORDER BY summary_date DESC
            LIMIT 1
        """
        summary_rows = databricks.fetch_all(summary_sql, {"uid": unit_id}).rows
        
        # Fetch assigned nurses
        nurses_sql = f"""
            SELECT n.provider_id, p.provider_name, p.employment_type, p.hourly_rate,
                   n.shift_start, n.shift_end
            FROM {fq_silver('nurse_assignment_current')} n
            JOIN {fq_gold('provider_360_flat')} p ON n.provider_id = p.provider_id
            WHERE n.unit_id = :uid
        """
        nurse_rows = databricks.fetch_all(nurses_sql, {"uid": unit_id}).rows
        
        # Build the response
        unit_data = {
            "unit_id": unit_row["unit_id"],
            "facility_id": unit_row["facility_id"],
            "facility_name": unit_row["facility_name"],
            "unit_name": unit_row["unit_name"],
            "unit_type": unit_row["unit_type"],
            "bed_count": unit_row["bed_count"],
            "target_ratio": float(unit_row["target_ratio"]),
        }
        
        if summary_rows:
            s = summary_rows[0]
            summary_data = {
                "summary_date": s["summary_date"],
                "unit_id": s["unit_id"],
                "facility_id": s["facility_id"],
                "facility_name": s["facility_name"],
                "unit_name": s["unit_name"],
                "unit_type": s["unit_type"],
                "bed_count": s["bed_count"],
                "current_census": s["current_census"],
                "target_ratio": float(s["target_ratio"]),
                "nurses_required": s["nurses_required"],
                "nurses_assigned": s["nurses_assigned"],
                "nurses_internal": s["nurses_internal"],
                "nurses_contract": s["nurses_contract"],
                "nurses_agency": s["nurses_agency"],
                "staffing_delta": s["staffing_delta"],
                "staffing_status": s["staffing_status"],
                "labor_cost_daily": float(s["labor_cost_daily"] or 0),
            }
        else:
            # Default summary if none exists
            summary_data = {
                "summary_date": date.today(),
                "unit_id": unit_row["unit_id"],
                "facility_id": unit_row["facility_id"],
                "facility_name": unit_row["facility_name"],
                "unit_name": unit_row["unit_name"],
                "unit_type": unit_row["unit_type"],
                "bed_count": unit_row["bed_count"],
                "current_census": 0,
                "target_ratio": float(unit_row["target_ratio"]),
                "nurses_required": 0,
                "nurses_assigned": 0,
                "nurses_internal": 0,
                "nurses_contract": 0,
                "nurses_agency": 0,
                "staffing_delta": 0,
                "staffing_status": "UNDERSTAFFED",
                "labor_cost_daily": 0.0,
            }
        
        assigned_nurses = []
        for nr in nurse_rows:
            assigned_nurses.append({
                "provider_id": nr["provider_id"],
                "provider_name": nr["provider_name"],
                "employment_type": nr["employment_type"],
                "hourly_rate": float(nr["hourly_rate"] or 50.0),
                "shift_start": nr["shift_start"],
                "shift_end": nr["shift_end"],
                "certifications": [],
                "missing_certifications": [],
                "is_fully_credentialed": True,
            })
        
        return {
            "unit": unit_data,
            "summary": summary_data,
            "assigned_nurses": assigned_nurses,
            "required_certifications": [],
        }

    def _mock():
        return mock_data.mock_unit_detail(unit_id)

    result = dbx_or_mock(lambda: databricks.with_retry(_run), _mock)
    if isinstance(result, UnitDetail):
        return result
    if result is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Unit {unit_id} not found")
    return UnitDetail.model_validate(result)


@router.get("/credential_gaps", response_model=PageResponse[CredentialGapRow])
def list_credential_gaps(
    facility_id: Optional[str] = None,
    unit_type: Optional[str] = Query(default=None, description="Comma-separated unit types"),
    gap_severity: Optional[str] = Query(default=None, description="Comma-separated: LOW,MEDIUM,HIGH,CRITICAL"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
):
    """List units where required certifications are missing among assigned nurses."""

    def _run():
        filters = []
        params = {}

        if facility_id:
            filters.append("facility_id = :fac")
            params["fac"] = facility_id

        if unit_type:
            unit_types = [t.strip() for t in unit_type.split(",") if t.strip()]
            placeholders = ", ".join([f":ut{i}" for i in range(len(unit_types))])
            filters.append(f"unit_type IN ({placeholders})")
            for i, ut in enumerate(unit_types):
                params[f"ut{i}"] = ut

        if gap_severity:
            severities = [s.strip() for s in gap_severity.split(",") if s.strip()]
            placeholders = ", ".join([f":gs{i}" for i in range(len(severities))])
            filters.append(f"gap_severity IN ({placeholders})")
            for i, gs in enumerate(severities):
                params[f"gs{i}"] = gs

        where_clause = " AND ".join(filters) if filters else "1=1"
        offset = (page - 1) * page_size
        params["limit"] = page_size
        params["offset"] = offset

        # This would be a computed view in production
        data_sql = f"""
            SELECT * FROM {fq_gold('credential_gaps')}
            WHERE {where_clause}
            ORDER BY gap_severity DESC, unit_name
            LIMIT :limit OFFSET :offset
        """
        count_sql = f"""
            SELECT COUNT(*) as cnt FROM {fq_gold('credential_gaps')}
            WHERE {where_clause}
        """
        return databricks.fetch_paged(data_sql, count_sql, params)

    def _mock():
        all_items = mock_data.mock_credential_gaps()
        items = all_items
        if facility_id:
            items = [r for r in items if r.facility_id == facility_id]
        if unit_type:
            allowed = {t.strip() for t in unit_type.split(",") if t.strip()}
            items = [r for r in items if r.unit_type in allowed]
        if gap_severity:
            allowed = {s.strip() for s in gap_severity.split(",") if s.strip()}
            items = [r for r in items if r.gap_severity in allowed]
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return (items[start:end], total)

    rows, total = dbx_or_mock(lambda: databricks.with_retry(_run), _mock)
    items = [CredentialGapRow.model_validate(r) if not isinstance(r, CredentialGapRow) else r for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/cost_breakdown", response_model=CostBreakdown)
def get_cost_breakdown(
    facility_id: Optional[str] = None,
    start_date: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
):
    """Get labor cost breakdown by employment type."""
    sd = parse_date(start_date) if start_date else date.today()
    ed = parse_date(end_date) if end_date else date.today()

    def _run():
        # Aggregate cost data from nurse_staffing_summary
        # The summary table has nurses_internal, nurses_contract, nurses_agency, and labor_cost_daily per unit
        facility_filter = "AND facility_id = :fac" if facility_id else ""
        sql = f"""
            SELECT
                COALESCE(SUM(nurses_internal), 0) as internal_count,
                COALESCE(SUM(nurses_contract), 0) as contract_count,
                COALESCE(SUM(nurses_agency), 0) as agency_count,
                COALESCE(SUM(nurses_assigned), 0) as total_nurses,
                COALESCE(SUM(labor_cost_daily), 0) as total_cost
            FROM {fq_gold('nurse_staffing_summary')}
            WHERE 1=1 {facility_filter}
        """
        params = {}
        if facility_id:
            params["fac"] = facility_id
        rows = databricks.fetch_all(sql, params).rows
        if not rows:
            return None
        row = rows[0]
        # Build CostBreakdown from aggregated data
        # Use standard hourly rates for estimation
        # Note: Databricks Row uses dict access, not .get()
        internal_count = int(row["internal_count"] or 0)
        contract_count = int(row["contract_count"] or 0)
        agency_count = int(row["agency_count"] or 0)
        total_cost = float(row["total_cost"] or 0)
        
        # Estimate costs by employment type (12-hour shifts assumed)
        internal_cost = internal_count * 50.0 * 12
        contract_cost = contract_count * 75.0 * 12
        agency_cost = agency_count * 95.0 * 12
        computed_total = internal_cost + contract_cost + agency_cost
        # Use DB total if available, otherwise computed total
        final_total = total_cost if total_cost > 0 else computed_total
        
        return {
            "facility_id": facility_id,
            "facility_name": None,
            "start_date": sd.isoformat(),
            "end_date": ed.isoformat(),
            "total_labor_cost": final_total,
            "breakdown_by_type": [
                {"employment_type": "INTERNAL", "nurse_count": internal_count, "total_hours": internal_count * 12.0, "total_cost": internal_cost, "avg_hourly_rate": 50.0, "percentage_of_total": (100.0 * internal_cost / final_total) if final_total > 0 else 0},
                {"employment_type": "CONTRACT", "nurse_count": contract_count, "total_hours": contract_count * 12.0, "total_cost": contract_cost, "avg_hourly_rate": 75.0, "percentage_of_total": (100.0 * contract_cost / final_total) if final_total > 0 else 0},
                {"employment_type": "AGENCY", "nurse_count": agency_count, "total_hours": agency_count * 12.0, "total_cost": agency_cost, "avg_hourly_rate": 95.0, "percentage_of_total": (100.0 * agency_cost / final_total) if final_total > 0 else 0},
            ],
            "internal_percentage": (100.0 * internal_cost / final_total) if final_total > 0 else 0,
            "outsourced_percentage": (100.0 * (contract_cost + agency_cost) / final_total) if final_total > 0 else 0,
        }

    def _mock():
        return mock_data.mock_cost_breakdown(facility_id=facility_id, start_date=sd, end_date=ed)

    row = dbx_or_mock(lambda: databricks.with_retry(_run), _mock)
    if isinstance(row, CostBreakdown):
        return row
    return CostBreakdown.model_validate(row)


@router.get("/forecast", response_model=PageResponse[CensusForecast])
def get_census_forecast(
    facility_id: Optional[str] = None,
    unit_type: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    """Get 7-day census forecasts by unit."""

    def _run():
        filters = []
        params = {"limit": page_size, "offset": (page - 1) * page_size}
        if facility_id:
            filters.append("facility_id = :fac")
            params["fac"] = facility_id
        if unit_type:
            filters.append("unit_type = :ut")
            params["ut"] = unit_type
        where = " AND ".join(filters) if filters else "1=1"
        
        data_sql = f"""
            SELECT * FROM {fq_gold('census_forecast')}
            WHERE {where}
            ORDER BY forecast_date, unit_name
            LIMIT :limit OFFSET :offset
        """
        count_sql = f"SELECT COUNT(*) as cnt FROM {fq_gold('census_forecast')} WHERE {where}"
        return databricks.fetch_paged(data_sql, count_sql, params)

    def _mock():
        # Generate mock forecast data
        from datetime import timedelta
        forecasts = []
        units = mock_data.mock_units()
        for i in range(1, 8):
            forecast_date = date.today() + timedelta(days=i)
            for u in units:
                if facility_id and u.facility_id != facility_id:
                    continue
                if unit_type and u.unit_type != unit_type:
                    continue
                census = int(u.bed_count * (0.7 + 0.1 * (i % 3)))
                forecasts.append(CensusForecast(
                    forecast_date=forecast_date, unit_id=u.unit_id, facility_id=u.facility_id,
                    facility_name=u.facility_name, unit_name=u.unit_name, unit_type=u.unit_type,
                    bed_count=u.bed_count, predicted_census=census,
                    predicted_occupancy_pct=round(census / u.bed_count * 100, 1),
                    nurses_required=max(1, int(census / u.target_ratio + 0.5)),
                    confidence_pct=85 - i * 2, is_weekend=forecast_date.weekday() >= 5))
        total = len(forecasts)
        start, end = (page - 1) * page_size, page * page_size
        return (forecasts[start:end], total)

    rows, total = dbx_or_mock(lambda: databricks.with_retry(_run), _mock)
    items = [CensusForecast.model_validate(r) if not isinstance(r, CensusForecast) else r for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/optimization", response_model=PageResponse[StaffingOptimization])
def get_staffing_optimization(
    facility_id: Optional[str] = None,
    priority: Optional[str] = Query(default=None, description="LOW,MEDIUM,HIGH"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    """Get auto-optimized staffing recommendations."""

    def _run():
        filters = []
        params = {"limit": page_size, "offset": (page - 1) * page_size}
        if facility_id:
            filters.append("facility_id = :fac")
            params["fac"] = facility_id
        if priority:
            filters.append("priority = :pri")
            params["pri"] = priority
        where = " AND ".join(filters) if filters else "1=1"
        
        data_sql = f"""
            SELECT * FROM {fq_gold('staffing_optimization')}
            WHERE {where}
            ORDER BY priority DESC, forecast_date, unit_name
            LIMIT :limit OFFSET :offset
        """
        count_sql = f"SELECT COUNT(*) as cnt FROM {fq_gold('staffing_optimization')} WHERE {where}"
        return databricks.fetch_paged(data_sql, count_sql, params)

    def _mock():
        from datetime import timedelta
        recs = []
        units = mock_data.mock_units()
        summaries = {s.unit_id: s for s in mock_data.mock_nurse_staffing_summary()}
        for i in range(1, 8):
            forecast_date = date.today() + timedelta(days=i)
            for u in units:
                if facility_id and u.facility_id != facility_id:
                    continue
                s = summaries.get(u.unit_id)
                census = int(u.bed_count * (0.7 + 0.1 * (i % 3)))
                required = max(1, int(census / u.target_ratio + 0.5))
                current = s.nurses_assigned if s else 0
                delta = required - current
                pri = "HIGH" if delta >= 2 else "MEDIUM" if delta > 0 else "LOW"
                if priority and pri != priority:
                    continue
                opt_internal = min(int(required * 0.6), s.nurses_internal if s else required)
                opt_contract = min(required - opt_internal, s.nurses_contract if s else 0)
                opt_agency = required - opt_internal - opt_contract
                opt_cost = (opt_internal * 50 + opt_contract * 75 + opt_agency * 95) * 12
                curr_cost = s.labor_cost_daily if s else opt_cost
                recs.append(StaffingOptimization(
                    forecast_date=forecast_date, unit_id=u.unit_id, facility_id=u.facility_id,
                    facility_name=u.facility_name, unit_name=u.unit_name, unit_type=u.unit_type,
                    predicted_census=census, nurses_required=required, current_staffed=current,
                    staffing_delta=delta, opt_internal=opt_internal, opt_contract=opt_contract,
                    opt_agency=opt_agency, opt_total=required, opt_daily_cost=opt_cost,
                    internal_pct=round(opt_internal / required * 100 if required else 0, 1),
                    outsourced_pct=round((opt_contract + opt_agency) / required * 100 if required else 0, 1),
                    current_daily_cost=curr_cost, cost_savings=curr_cost - opt_cost,
                    action=f"STAFF_UP: Add {delta}" if delta > 0 else "OPTIMAL",
                    priority=pri, confidence_pct=85 - i * 2))
        total = len(recs)
        start, end = (page - 1) * page_size, page * page_size
        return (recs[start:end], total)

    rows, total = dbx_or_mock(lambda: databricks.with_retry(_run), _mock)
    items = [StaffingOptimization.model_validate(r) if not isinstance(r, StaffingOptimization) else r for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/optimization/summary", response_model=OptimizationSummary)
def get_optimization_summary(facility_id: Optional[str] = None):
    """Get 7-day optimization outlook summary."""

    def _run():
        facility_filter = "AND facility_id = :fac" if facility_id else ""
        sql = f"""
            SELECT
                COALESCE(SUM(nurses_required), 0) as total_nurses_needed,
                COALESCE(SUM(opt_daily_cost), 0) as total_optimized_cost,
                COALESCE(SUM(cost_savings), 0) as total_potential_savings,
                SUM(CASE WHEN staffing_delta > 0 THEN 1 ELSE 0 END) as units_needing_attention,
                SUM(CASE WHEN priority = 'HIGH' THEN 1 ELSE 0 END) as high_priority_count,
                COUNT(DISTINCT forecast_date) as forecast_days
            FROM {fq_gold('staffing_optimization')}
            WHERE 1=1 {facility_filter}
        """
        params = {"fac": facility_id} if facility_id else {}
        rows = databricks.fetch_all(sql, params).rows
        return rows[0] if rows else None

    def _mock():
        return OptimizationSummary(
            total_nurses_needed=420, total_optimized_cost=176400.0, total_potential_savings=12600.0,
            units_needing_attention=15, high_priority_count=4, forecast_days=7)

    row = dbx_or_mock(lambda: databricks.with_retry(_run), _mock)
    if isinstance(row, OptimizationSummary):
        return row
    return OptimizationSummary.model_validate(row)
