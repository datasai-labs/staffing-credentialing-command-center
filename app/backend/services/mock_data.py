from __future__ import annotations
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from models.credentials import CredentialRiskRow
from models.kpis import KpiSummaryDaily
from models.providers import Provider360, ProviderDetailResponse, ProviderMini
from models.staffing import ShiftRecommendations, StaffingGap
from models.actions import CreateRiskActionRequest, RiskAction, UpdateRiskActionRequest
from models.summaries import (
    CredentialRiskSummaryResponse, CountByLabel, DateCount, DateValue,
    KpiTrendPoint, KpiTrendResponse, ProvidersSummaryResponse, ShiftPredictionResponse, StaffingSummaryResponse,
)
from models.nurse_staffing import (
    CostBreakdown, CostBreakdownItem, CredentialGapRow, NurseAssignment,
    NurseStaffingKpis, NurseStaffingSummary, Unit, UnitDetail,
)

_now = lambda: datetime.now(timezone.utc)

# ─────────────────────────────────────────────────────────────────────────────
# KPIs
# ─────────────────────────────────────────────────────────────────────────────

def mock_kpis() -> KpiSummaryDaily:
    return KpiSummaryDaily(kpi_date=date.today(), providers_total=200, providers_pending=27,
                           providers_expiring_30d=14, daily_revenue_at_risk_est=105000.0, last_built_at=_now())

def mock_kpis_trend(days: int = 30) -> KpiTrendResponse:
    pts = [KpiTrendPoint(kpi_date=date.today() - timedelta(days=days - 1 - i),
                         providers_pending=max(0, 20 + (i % 7) - 3),
                         providers_expiring_30d=max(0, 12 + (i % 5) - 2),
                         daily_revenue_at_risk_est=90000.0 + (i % 9) * 2500.0) for i in range(days)]
    return KpiTrendResponse(days=days, points=pts)

# ─────────────────────────────────────────────────────────────────────────────
# Providers
# ─────────────────────────────────────────────────────────────────────────────

_PROVIDERS = [
    ("PROV-001", "Alex Morgan", "Emergency Medicine", "FAC-001", "Manhattan General", "ACTIVE", 21, 68, 2, 1, 2),
    ("PROV-002", "Jordan Lee", "Surgery", "FAC-002", "Brooklyn Community", "ACTIVE", 120, 10, 3, 2, 3),
    ("PROV-003", "Taylor Kim", "Critical Care", "FAC-003", "Queens Regional", "ON_LEAVE", -5, 200, 0, 0, 1),
]

def mock_providers() -> list[Provider360]:
    now = _now()
    return [Provider360(
        provider_id=pid, provider_name=name, specialty=spec, home_facility_id=fid,
        hired_at=date(2022, 6, 15), provider_status=status, created_at=now - timedelta(days=300),
        home_facility_name=fname, state_license_status="ACTIVE" if lic > 0 else "EXPIRED",
        state_license_days_left=lic, acls_status="ACTIVE" if acls > 0 else "PENDING_REVIEW",
        acls_days_left=acls, active_privilege_count=priv, active_privilege_facility_count=pfac,
        active_payer_count=payer, last_built_at=now
    ) for pid, name, spec, fid, fname, status, lic, acls, priv, pfac, payer in _PROVIDERS]

def mock_provider_detail(provider_id: str) -> ProviderDetailResponse:
    providers = {p.provider_id: p for p in mock_providers()}
    p = providers.get(provider_id, mock_providers()[0])
    now = _now()
    
    def _risk_bucket(days: int) -> str:
        return "EXPIRED" if days < 0 else "0-14" if days <= 14 else "15-30" if days <= 30 else ">90"
    
    risks = [
        CredentialRiskRow(event_id=f"EVT-{p.provider_id}-LIC", provider_id=p.provider_id, cred_type="STATE_MED_LICENSE",
                          issued_at=now - timedelta(days=650), expires_at=now + timedelta(days=p.state_license_days_left or 30),
                          verified_at=now - timedelta(days=640), source_system="CRED_SYS_A",
                          cred_status=str(p.state_license_status), ingested_at=now - timedelta(hours=1),
                          days_until_expiration=p.state_license_days_left or 30, risk_bucket=_risk_bucket(p.state_license_days_left or 30), last_built_at=now),
        CredentialRiskRow(event_id=f"EVT-{p.provider_id}-ACLS", provider_id=p.provider_id, cred_type="ACLS",
                          issued_at=now - timedelta(days=350), expires_at=now + timedelta(days=p.acls_days_left or 60),
                          verified_at=None, source_system="CRED_SYS_B", cred_status=str(p.acls_status),
                          ingested_at=now - timedelta(hours=2), days_until_expiration=p.acls_days_left or 60,
                          risk_bucket=_risk_bucket(p.acls_days_left or 60), last_built_at=now),
    ]
    return ProviderDetailResponse(provider=p, credential_risk_rows=risks)

# ─────────────────────────────────────────────────────────────────────────────
# Staffing Gaps
# ─────────────────────────────────────────────────────────────────────────────

_GAPS = [
    ("SHIFT-001", "FAC-001", "Manhattan General", 1, "PROC-ER-SEDS", "Moderate Sedation", 2, 0, 1, "Unfilled shift", "HIGH"),
    ("SHIFT-002", "FAC-002", "Brooklyn Community", 2, "PROC-CARD-ECG", "ECG Interpretation", 1, 1, 5, "OK", "LOW"),
    ("SHIFT-003", "FAC-001", "Manhattan General", 1, "PROC-CATH-001", "Cardiac Catheterization", 2, 0, 0, "No credentialed providers", "CRITICAL"),
    ("SHIFT-004", "FAC-003", "Queens Regional", 2, "PROC-ICU-VENT", "Ventilator Management", 3, 0, 0, "No credentialed providers", "CRITICAL"),
    ("SHIFT-005", "FAC-002", "Brooklyn Community", 3, "PROC-STROKE-001", "Stroke Protocol", 1, 0, 0, "All providers expired ACLS", "CRITICAL"),
    ("SHIFT-006", "FAC-001", "Manhattan General", 4, "PROC-OR-SURG", "General Surgery Coverage", 2, 0, 0, "No active surgical privileges", "CRITICAL"),
]

def mock_staffing_gaps() -> list[StaffingGap]:
    now = _now()
    return [StaffingGap(
        shift_id=sid, facility_id=fid, facility_name=fname,
        start_ts=now + timedelta(days=d, hours=6), end_ts=now + timedelta(days=d, hours=18),
        required_procedure_code=proc, procedure_name=pname, required_count=req, assigned_count=asgn,
        eligible_provider_count=elig, gap_count=req - asgn, risk_reason=reason, risk_level=risk, last_built_at=now
    ) for sid, fid, fname, d, proc, pname, req, asgn, elig, reason, risk in _GAPS]

def mock_staffing_summary() -> StaffingSummaryResponse:
    gaps = mock_staffing_gaps()
    by_risk = {}
    daily = {}
    for g in gaps:
        by_risk[g.risk_level] = by_risk.get(g.risk_level, 0) + 1
        daily[g.start_ts.date()] = daily.get(g.start_ts.date(), 0) + g.gap_count
    return StaffingSummaryResponse(
        by_risk_level=[CountByLabel(label=k, count=v) for k, v in sorted(by_risk.items())],
        daily_gap_count=[DateValue(date=k, value=v) for k, v in sorted(daily.items())],
        top_facilities=[{"facility_id": g.facility_id, "facility_name": g.facility_name, "total_gap_count": g.gap_count, "shift_count": 1} for g in gaps],
        top_procedures=[{"required_procedure_code": g.required_procedure_code, "procedure_name": g.procedure_name, "total_gap_count": g.gap_count, "shift_count": 1} for g in gaps],
    )

def mock_shift_recommendations(shift_id: str) -> ShiftRecommendations:
    return ShiftRecommendations(shift_id=shift_id, recommended_provider_ids=["PROV-001", "PROV-002"],
        recommended_providers=[ProviderMini(provider_id="PROV-001", provider_name="Alex Morgan", specialty="Emergency Medicine", provider_status="ACTIVE"),
                              ProviderMini(provider_id="PROV-002", provider_name="Jordan Lee", specialty="Surgery", provider_status="ACTIVE")])

def mock_shift_prediction(shift_id: str) -> ShiftPredictionResponse:
    return ShiftPredictionResponse(shift_id=shift_id, predicted_gap_prob=0.72, predicted_is_gap=1, scored_at=_now())

# ─────────────────────────────────────────────────────────────────────────────
# Credential Risk
# ─────────────────────────────────────────────────────────────────────────────

def mock_credential_risk() -> list[CredentialRiskRow]:
    now = _now()
    data = [
        ("EVT-PROV-001-LIC", "PROV-001", "STATE_MED_LICENSE", 700, 21, "CRED_SYS_A", "ACTIVE", "15-30"),
        ("EVT-PROV-002-ACLS", "PROV-002", "ACLS", 400, 10, "CRED_SYS_B", "PENDING_REVIEW", "0-14"),
        ("EVT-PROV-003-LIC", "PROV-003", "STATE_MED_LICENSE", 900, -5, "CRED_SYS_A", "EXPIRED", "EXPIRED"),
    ]
    return [CredentialRiskRow(
        event_id=eid, provider_id=pid, cred_type=ctype, issued_at=now - timedelta(days=issued),
        expires_at=now + timedelta(days=exp), verified_at=now - timedelta(days=issued - 10) if exp > 0 else None,
        source_system=src, cred_status=status, ingested_at=now - timedelta(hours=1),
        days_until_expiration=exp, risk_bucket=bucket, last_built_at=now
    ) for eid, pid, ctype, issued, exp, src, status, bucket in data]

def mock_credential_risk_summary() -> CredentialRiskSummaryResponse:
    rows = mock_credential_risk()
    by_bucket, by_type, by_week = {}, {}, {}
    for r in rows:
        by_bucket[r.risk_bucket] = by_bucket.get(r.risk_bucket, 0) + 1
        by_type[r.cred_type] = by_type.get(r.cred_type, 0) + 1
        wk = r.expires_at.date() - timedelta(days=r.expires_at.date().weekday())
        by_week[wk] = by_week.get(wk, 0) + 1
    return CredentialRiskSummaryResponse(
        by_bucket=[CountByLabel(label=k, count=v) for k, v in by_bucket.items()],
        by_cred_type=[CountByLabel(label=k, count=v) for k, v in by_type.items()],
        expires_by_week=[DateCount(date=k, count=v) for k, v in sorted(by_week.items())],
    )

def mock_providers_summary() -> ProvidersSummaryResponse:
    providers = mock_providers()
    by_spec = {}
    for p in providers:
        by_spec[p.specialty] = by_spec.get(p.specialty, 0) + 1
    
    min_days = lambda p: min(p.state_license_days_left or 999999, p.acls_days_left or 999999)
    funnel = {"<=14": sum(1 for p in providers if min_days(p) <= 14),
              "<=30": sum(1 for p in providers if min_days(p) <= 30),
              "<=90": sum(1 for p in providers if min_days(p) <= 90)}
    
    readiness = lambda p: sum([p.provider_status == "ACTIVE", (p.state_license_days_left or -1) >= 0,
                               (p.acls_days_left or -1) >= 0, p.active_payer_count > 0, p.active_privilege_count > 0])
    hist = {}
    for p in providers:
        s = str(readiness(p))
        hist[s] = hist.get(s, 0) + 1
    
    return ProvidersSummaryResponse(
        by_specialty=[CountByLabel(label=k, count=v) for k, v in by_spec.items()],
        expiring_funnel=[CountByLabel(label=k, count=v) for k, v in funnel.items()],
        readiness_histogram=[CountByLabel(label=k, count=v) for k, v in sorted(hist.items(), key=lambda x: int(x[0]))],
    )

# ─────────────────────────────────────────────────────────────────────────────
# Actions (local store)
# ─────────────────────────────────────────────────────────────────────────────

_ACTIONS_STORE: dict[str, RiskAction] = {}

def _seed_actions():
    if _ACTIONS_STORE:
        return
    now = _now()
    for aid, etype, eid, fid, atype, status, prio, owner, hours, notes in [
        ("ACT-001", "SHIFT", "SHIFT-001", "FAC-001", "OUTREACH", "OPEN", "HIGH", "staffing_coordinator", 18, "Confirm per-diem availability"),
        ("ACT-002", "PROVIDER", "PROV-002", "FAC-002", "CREDENTIAL_EXPEDITE", "IN_PROGRESS", "HIGH", "med_staff_office", 48, "ACLS expiring soon"),
    ]:
        _ACTIONS_STORE[aid] = RiskAction(action_id=aid, entity_type=etype, entity_id=eid, facility_id=fid,
            action_type=atype, status=status, priority=prio, owner=owner, created_at=now - timedelta(hours=hours),
            updated_at=now - timedelta(hours=2), resolved_at=None, notes=notes, last_built_at=now)

def mock_actions_page(*, entity_type: Optional[str] = None, entity_id: Optional[str] = None, status: Optional[str] = None,
                      action_type: Optional[str] = None, facility_id: Optional[str] = None, page: int = 1, page_size: int = 50):
    from models.common import PageResponse
    _seed_actions()
    items = [a for a in _ACTIONS_STORE.values()
             if (not entity_type or a.entity_type == entity_type) and (not entity_id or a.entity_id == entity_id)
             and (not status or a.status == status) and (not action_type or a.action_type == action_type)
             and (not facility_id or a.facility_id == facility_id)]
    items.sort(key=lambda a: a.updated_at, reverse=True)
    start = (page - 1) * page_size
    return PageResponse[RiskAction](items=items[start:start + page_size], total=len(items), page=page, page_size=page_size)

def mock_actions_create(payload: CreateRiskActionRequest) -> RiskAction:
    _seed_actions()
    now = _now()
    aid = f"ACT-{len(_ACTIONS_STORE) + 1:03d}"
    a = RiskAction(action_id=aid, entity_type=payload.entity_type, entity_id=payload.entity_id,
                   facility_id=payload.facility_id, action_type=payload.action_type, status="OPEN",
                   priority=payload.priority, owner=payload.owner, created_at=now, updated_at=now,
                   resolved_at=None, notes=payload.notes, last_built_at=now)
    _ACTIONS_STORE[aid] = a
    return a

def mock_actions_update(action_id: str, payload: UpdateRiskActionRequest) -> RiskAction:
    _seed_actions()
    now = _now()
    a = _ACTIONS_STORE.get(action_id) or RiskAction(action_id=action_id, entity_type="SHIFT", entity_id="SHIFT-001",
        facility_id="FAC-001", action_type="OUTREACH", status="OPEN", priority="MEDIUM", owner=None,
        created_at=now - timedelta(hours=1), updated_at=now, resolved_at=None, notes=None, last_built_at=now)
    
    data = a.model_dump()
    for k, v in [("status", payload.status), ("priority", payload.priority), ("owner", payload.owner), ("notes", payload.notes)]:
        if v is not None:
            data[k] = v
    if payload.status == "RESOLVED":
        data["resolved_at"] = now
    data["updated_at"] = data["last_built_at"] = now
    
    updated = RiskAction.model_validate(data)
    _ACTIONS_STORE[action_id] = updated
    return updated

# ─────────────────────────────────────────────────────────────────────────────
# Nurse Staffing
# ─────────────────────────────────────────────────────────────────────────────

_UNITS = [
    ("UNIT-ICU-001", "FAC-001", "Manhattan General", "ICU Tower A", "ICU", 20, 2.0),
    ("UNIT-ICU-002", "FAC-002", "Brooklyn Community", "ICU West", "ICU", 16, 2.0),
    ("UNIT-MEDSURG-001", "FAC-001", "Manhattan General", "Med-Surg 3rd Floor", "MED_SURG", 40, 5.0),
    ("UNIT-MEDSURG-002", "FAC-002", "Brooklyn Community", "Med-Surg East", "MED_SURG", 32, 5.0),
    ("UNIT-TELE-001", "FAC-001", "Manhattan General", "Telemetry Unit", "TELEMETRY", 24, 4.0),
    ("UNIT-ED-001", "FAC-001", "Manhattan General", "Emergency Department", "ED", 30, 4.0),
    ("UNIT-ED-002", "FAC-002", "Brooklyn Community", "Emergency Room", "ED", 24, 4.0),
    ("UNIT-STEPDOWN-001", "FAC-001", "Manhattan General", "Step-Down Unit", "STEP_DOWN", 18, 3.0),
    ("UNIT-OR-001", "FAC-001", "Manhattan General", "Operating Rooms", "OR", 12, 1.0),
    ("UNIT-NICU-001", "FAC-003", "Queens Regional", "Neonatal ICU", "NICU", 24, 2.0),
]

def mock_units() -> list[Unit]:
    return [Unit(unit_id=uid, facility_id=fid, facility_name=fname, unit_name=uname,
                 unit_type=utype, bed_count=beds, target_ratio=ratio) for uid, fid, fname, uname, utype, beds, ratio in _UNITS]

_STAFFING = [
    ("UNIT-ICU-001", 18, 8, 5, 2, 1, "UNDERSTAFFED"),
    ("UNIT-ICU-002", 12, 6, 4, 1, 1, "OPTIMAL"),
    ("UNIT-MEDSURG-001", 30, 7, 4, 2, 1, "OVERSTAFFED"),
    ("UNIT-MEDSURG-002", 28, 4, 2, 1, 1, "UNDERSTAFFED"),
    ("UNIT-TELE-001", 20, 5, 3, 1, 1, "OPTIMAL"),
    ("UNIT-ED-001", 25, 5, 3, 1, 1, "UNDERSTAFFED"),
    ("UNIT-ED-002", 18, 5, 2, 2, 1, "OVERSTAFFED"),
    ("UNIT-STEPDOWN-001", 15, 4, 2, 1, 1, "UNDERSTAFFED"),
    ("UNIT-OR-001", 10, 10, 7, 2, 1, "OPTIMAL"),
    ("UNIT-NICU-001", 20, 8, 5, 2, 1, "UNDERSTAFFED"),
]

def mock_nurse_staffing_summary() -> list[NurseStaffingSummary]:
    now, today = _now(), date.today()
    unit_map = {u.unit_id: u for u in mock_units()}
    
    summaries = []
    for uid, census, assigned, internal, contract, agency, status in _STAFFING:
        u = unit_map.get(uid)
        if not u:
            continue
        required = max(1, round(census / u.target_ratio))
        labor = (internal * 50 + contract * 75 + agency * 95) * 12
        summaries.append(NurseStaffingSummary(
            summary_date=today, unit_id=u.unit_id, facility_id=u.facility_id, facility_name=u.facility_name,
            unit_name=u.unit_name, unit_type=u.unit_type, bed_count=u.bed_count, current_census=census,
            target_ratio=u.target_ratio, nurses_required=required, nurses_assigned=assigned,
            nurses_internal=internal, nurses_contract=contract, nurses_agency=agency,
            staffing_delta=assigned - required, staffing_status=status, labor_cost_daily=float(labor), last_built_at=now))
    return summaries

def mock_nurse_staffing_kpis(facility_id: Optional[str] = None) -> NurseStaffingKpis:
    summaries = [s for s in mock_nurse_staffing_summary() if not facility_id or s.facility_id == facility_id]
    total = sum(s.nurses_assigned for s in summaries)
    outsourced = sum(s.nurses_contract + s.nurses_agency for s in summaries)
    return NurseStaffingKpis(
        kpi_date=date.today(), total_nurses_on_shift=total,
        units_understaffed=sum(1 for s in summaries if s.staffing_status == "UNDERSTAFFED"),
        units_optimal=sum(1 for s in summaries if s.staffing_status == "OPTIMAL"),
        units_overstaffed=sum(1 for s in summaries if s.staffing_status == "OVERSTAFFED"),
        agency_contract_percentage=round(100.0 * outsourced / total, 1) if total else 0.0,
        daily_labor_cost=sum(s.labor_cost_daily for s in summaries),
        credential_gaps_count=len(mock_credential_gaps()), last_built_at=_now())

_CRED_GAPS = [
    ("UNIT-ICU-001", "FAC-001", "Manhattan General", "ICU Tower A", "ICU", "ACLS", 8, 6, 2, "HIGH", ["NURSE-012", "NURSE-015"]),
    ("UNIT-ICU-001", "FAC-001", "Manhattan General", "ICU Tower A", "ICU", "Critical Care Certification", 8, 5, 3, "CRITICAL", ["NURSE-012", "NURSE-015", "NURSE-018"]),
    ("UNIT-ED-001", "FAC-001", "Manhattan General", "Emergency Department", "ED", "TNCC", 5, 3, 2, "MEDIUM", ["NURSE-022", "NURSE-025"]),
    ("UNIT-NICU-001", "FAC-003", "Queens Regional", "Neonatal ICU", "NICU", "NRP", 8, 6, 2, "HIGH", ["NURSE-031", "NURSE-034"]),
    ("UNIT-STEPDOWN-001", "FAC-001", "Manhattan General", "Step-Down Unit", "STEP_DOWN", "ACLS", 4, 3, 1, "LOW", ["NURSE-041"]),
]

def mock_credential_gaps() -> list[CredentialGapRow]:
    return [CredentialGapRow(unit_id=uid, facility_id=fid, facility_name=fname, unit_name=uname, unit_type=utype,
                             required_cred_type=cred, nurses_assigned=asgn, nurses_with_cert=with_cert,
                             nurses_missing_cert=missing, gap_severity=sev, affected_nurse_ids=ids)
            for uid, fid, fname, uname, utype, cred, asgn, with_cert, missing, sev, ids in _CRED_GAPS]

_UNIT_CERTS = {
    "ICU": ["ACLS", "BLS", "Critical Care Certification"], "STEP_DOWN": ["ACLS", "BLS"], "MED_SURG": ["BLS"],
    "TELEMETRY": ["ACLS", "BLS"], "ED": ["ACLS", "BLS", "TNCC", "PALS"], "OR": ["BLS", "ACLS"],
    "L_AND_D": ["BLS", "NRP"], "PSYCH": ["BLS", "CPI"], "NICU": ["BLS", "NRP"], "PACU": ["ACLS", "BLS"],
}

def mock_unit_detail(unit_id: str) -> UnitDetail:
    now = _now()
    units, summaries = mock_units(), mock_nurse_staffing_summary()
    unit = next((u for u in units if u.unit_id == unit_id), units[0])
    summary = next((s for s in summaries if s.unit_id == unit_id), summaries[0])
    
    rates = {"INTERNAL": 50.0, "CONTRACT": 75.0, "AGENCY": 95.0}
    emp_types = ["INTERNAL"] * summary.nurses_internal + ["CONTRACT"] * summary.nurses_contract + ["AGENCY"] * summary.nurses_agency
    required = _UNIT_CERTS.get(unit.unit_type, ["BLS"])
    
    nurses = [NurseAssignment(
        provider_id=f"NURSE-{unit_id[-3:]}-{i+1:02d}", provider_name=f"Nurse {chr(65+i)} ({et.title()})",
        employment_type=et, hourly_rate=rates[et],
        shift_start=now.replace(hour=7, minute=0, second=0, microsecond=0),
        shift_end=now.replace(hour=19, minute=0, second=0, microsecond=0),
        certifications=required if i < len(emp_types) - 2 else required[:-1],
        missing_certifications=[] if i < len(emp_types) - 2 else [required[-1]],
        is_fully_credentialed=i < len(emp_types) - 2
    ) for i, et in enumerate(emp_types)]
    
    return UnitDetail(unit=unit, summary=summary, assigned_nurses=nurses, required_certifications=required)

def mock_cost_breakdown(facility_id: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None) -> CostBreakdown:
    summaries = [s for s in mock_nurse_staffing_summary() if not facility_id or s.facility_id == facility_id]
    counts = {"INTERNAL": sum(s.nurses_internal for s in summaries),
              "CONTRACT": sum(s.nurses_contract for s in summaries),
              "AGENCY": sum(s.nurses_agency for s in summaries)}
    rates = {"INTERNAL": 50.0, "CONTRACT": 75.0, "AGENCY": 95.0}
    costs = {k: counts[k] * rates[k] * 12 for k in counts}
    total = sum(costs.values())
    
    breakdown = [CostBreakdownItem(employment_type=k, nurse_count=counts[k], total_hours=counts[k] * 12.0,
                                   total_cost=costs[k], avg_hourly_rate=rates[k],
                                   percentage_of_total=round(100.0 * costs[k] / total, 1) if total else 0.0)
                 for k in ["INTERNAL", "CONTRACT", "AGENCY"]]
    
    fac_names = {"FAC-001": "Manhattan General", "FAC-002": "Brooklyn Community", "FAC-003": "Queens Regional"}
    return CostBreakdown(facility_id=facility_id, facility_name=fac_names.get(facility_id) if facility_id else None,
                         start_date=start_date or date.today(), end_date=end_date or date.today(),
                         total_labor_cost=total, breakdown_by_type=breakdown,
                         internal_percentage=round(100.0 * costs["INTERNAL"] / total, 1) if total else 0.0,
                         outsourced_percentage=round(100.0 * (costs["CONTRACT"] + costs["AGENCY"]) / total, 1) if total else 0.0)
