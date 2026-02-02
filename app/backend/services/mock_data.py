from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from models.credentials import CredentialRiskRow
from models.kpis import KpiSummaryDaily
from models.providers import Provider360, ProviderDetailResponse, ProviderMini
from models.staffing import ShiftRecommendations, StaffingGap
from models.actions import CreateRiskActionRequest, RiskAction, UpdateRiskActionRequest
from models.summaries import (
    CredentialRiskSummaryResponse,
    CountByLabel,
    DateCount,
    DateValue,
    KpiTrendPoint,
    KpiTrendResponse,
    ProvidersSummaryResponse,
    ShiftPredictionResponse,
    StaffingSummaryResponse,
)
from models.nurse_staffing import (
    CostBreakdown,
    CostBreakdownItem,
    CredentialGapRow,
    NurseAssignment,
    NurseStaffingKpis,
    NurseStaffingSummary,
    Unit,
    UnitDetail,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def mock_kpis() -> KpiSummaryDaily:
    now = _now()
    return KpiSummaryDaily(
        kpi_date=date.today(),
        providers_total=200,
        providers_pending=27,
        providers_expiring_30d=14,
        daily_revenue_at_risk_est=105000.0,
        last_built_at=now,
    )


def mock_kpis_trend(days: int = 30) -> KpiTrendResponse:
    now = _now()
    pts = []
    for i in range(days):
        d = date.today() - timedelta(days=(days - 1 - i))
        pts.append(
            KpiTrendPoint(
                kpi_date=d,
                providers_pending=max(0, 20 + (i % 7) - 3),
                providers_expiring_30d=max(0, 12 + (i % 5) - 2),
                daily_revenue_at_risk_est=90000.0 + float((i % 9) * 2500.0),
            )
        )
    return KpiTrendResponse(days=days, points=pts)


def mock_providers() -> list[Provider360]:
    now = _now()
    return [
        Provider360(
            provider_id="PROV-001",
            provider_name="Alex Morgan",
            specialty="Emergency Medicine",
            home_facility_id="FAC-001",
            hired_at=date(2022, 6, 15),
            provider_status="ACTIVE",
            created_at=now - timedelta(days=300),
            home_facility_name="Manhattan General",
            state_license_status="ACTIVE",
            state_license_days_left=21,
            acls_status="ACTIVE",
            acls_days_left=68,
            active_privilege_count=2,
            active_privilege_facility_count=1,
            active_payer_count=2,
            last_built_at=now,
        ),
        Provider360(
            provider_id="PROV-002",
            provider_name="Jordan Lee",
            specialty="Surgery",
            home_facility_id="FAC-002",
            hired_at=date(2020, 2, 1),
            provider_status="ACTIVE",
            created_at=now - timedelta(days=700),
            home_facility_name="Brooklyn Community",
            state_license_status="ACTIVE",
            state_license_days_left=120,
            acls_status="PENDING_REVIEW",
            acls_days_left=10,
            active_privilege_count=3,
            active_privilege_facility_count=2,
            active_payer_count=3,
            last_built_at=now,
        ),
        Provider360(
            provider_id="PROV-003",
            provider_name="Taylor Kim",
            specialty="Critical Care",
            home_facility_id="FAC-003",
            hired_at=date(2019, 9, 20),
            provider_status="ON_LEAVE",
            created_at=now - timedelta(days=1000),
            home_facility_name="Queens Regional",
            state_license_status="EXPIRED",
            state_license_days_left=-5,
            acls_status="ACTIVE",
            acls_days_left=200,
            active_privilege_count=0,
            active_privilege_facility_count=0,
            active_payer_count=1,
            last_built_at=now,
        ),
    ]


def mock_provider_detail(provider_id: str) -> ProviderDetailResponse:
    providers = {p.provider_id: p for p in mock_providers()}
    p = providers.get(provider_id) or mock_providers()[0]
    now = _now()
    risks = [
        CredentialRiskRow(
            event_id=f"EVT-{provider_id}-LIC",
            provider_id=p.provider_id,
            cred_type="STATE_MED_LICENSE",
            issued_at=now - timedelta(days=650),
            expires_at=now + timedelta(days=int(p.state_license_days_left or 30)),
            verified_at=now - timedelta(days=640),
            source_system="CRED_SYS_A",
            cred_status=str(p.state_license_status or "ACTIVE"),
            ingested_at=now - timedelta(hours=1),
            days_until_expiration=int(p.state_license_days_left or 30),
            risk_bucket="0-14" if (p.state_license_days_left or 9999) <= 14 else "15-30" if (p.state_license_days_left or 9999) <= 30 else ">90",
            last_built_at=now,
        ),
        CredentialRiskRow(
            event_id=f"EVT-{provider_id}-ACLS",
            provider_id=p.provider_id,
            cred_type="ACLS",
            issued_at=now - timedelta(days=350),
            expires_at=now + timedelta(days=int(p.acls_days_left or 60)),
            verified_at=None,
            source_system="CRED_SYS_B",
            cred_status=str(p.acls_status or "ACTIVE"),
            ingested_at=now - timedelta(hours=2),
            days_until_expiration=int(p.acls_days_left or 60),
            risk_bucket="0-14" if (p.acls_days_left or 9999) <= 14 else "15-30" if (p.acls_days_left or 9999) <= 30 else "31-90",
            last_built_at=now,
        ),
    ]
    return ProviderDetailResponse(provider=p, credential_risk_rows=risks)


def mock_staffing_gaps() -> list[StaffingGap]:
    now = _now()
    return [
        StaffingGap(
            shift_id="SHIFT-001",
            facility_id="FAC-001",
            facility_name="Manhattan General",
            start_ts=now + timedelta(days=1),
            end_ts=now + timedelta(days=1, hours=12),
            required_procedure_code="PROC-ER-SEDS",
            procedure_name="Moderate Sedation",
            required_count=2,
            assigned_count=0,
            eligible_provider_count=1,
            gap_count=2,
            risk_reason="Unfilled shift",
            risk_level="HIGH",
            last_built_at=now,
        ),
        StaffingGap(
            shift_id="SHIFT-002",
            facility_id="FAC-002",
            facility_name="Brooklyn Community",
            start_ts=now + timedelta(days=2),
            end_ts=now + timedelta(days=2, hours=12),
            required_procedure_code="PROC-CARD-ECG",
            procedure_name="ECG Interpretation",
            required_count=1,
            assigned_count=1,
            eligible_provider_count=5,
            gap_count=0,
            risk_reason="OK",
            risk_level="LOW",
            last_built_at=now,
        ),
        # Critical shifts with NO eligible providers - for Scenario Planner
        StaffingGap(
            shift_id="SHIFT-003",
            facility_id="FAC-001",
            facility_name="Manhattan General",
            start_ts=now + timedelta(days=1, hours=6),
            end_ts=now + timedelta(days=1, hours=18),
            required_procedure_code="PROC-CATH-001",
            procedure_name="Cardiac Catheterization",
            required_count=2,
            assigned_count=0,
            eligible_provider_count=0,
            gap_count=2,
            risk_reason="No credentialed providers available",
            risk_level="CRITICAL",
            last_built_at=now,
        ),
        StaffingGap(
            shift_id="SHIFT-004",
            facility_id="FAC-003",
            facility_name="Queens Regional",
            start_ts=now + timedelta(days=2, hours=8),
            end_ts=now + timedelta(days=2, hours=20),
            required_procedure_code="PROC-ICU-VENT",
            procedure_name="Ventilator Management",
            required_count=3,
            assigned_count=0,
            eligible_provider_count=0,
            gap_count=3,
            risk_reason="No credentialed providers available",
            risk_level="CRITICAL",
            last_built_at=now,
        ),
        StaffingGap(
            shift_id="SHIFT-005",
            facility_id="FAC-002",
            facility_name="Brooklyn Community",
            start_ts=now + timedelta(days=3),
            end_ts=now + timedelta(days=3, hours=12),
            required_procedure_code="PROC-STROKE-001",
            procedure_name="Stroke Protocol",
            required_count=1,
            assigned_count=0,
            eligible_provider_count=0,
            gap_count=1,
            risk_reason="All providers expired ACLS",
            risk_level="CRITICAL",
            last_built_at=now,
        ),
        StaffingGap(
            shift_id="SHIFT-006",
            facility_id="FAC-001",
            facility_name="Manhattan General",
            start_ts=now + timedelta(days=4),
            end_ts=now + timedelta(days=4, hours=12),
            required_procedure_code="PROC-OR-SURG",
            procedure_name="General Surgery Coverage",
            required_count=2,
            assigned_count=0,
            eligible_provider_count=0,
            gap_count=2,
            risk_reason="Privilege gaps - no active surgical privileges",
            risk_level="CRITICAL",
            last_built_at=now,
        ),
    ]


def mock_staffing_summary() -> StaffingSummaryResponse:
    gaps = mock_staffing_gaps()
    by_risk = {}
    for g in gaps:
        by_risk[g.risk_level] = by_risk.get(g.risk_level, 0) + 1
    by_risk_level = [CountByLabel(label=k, count=v) for k, v in sorted(by_risk.items(), key=lambda kv: kv[0])]
    daily = {}
    for g in gaps:
        dt = g.start_ts.date()
        daily[dt] = daily.get(dt, 0.0) + float(g.gap_count)
    daily_gap_count = [DateValue(date=k, value=v) for k, v in sorted(daily.items(), key=lambda kv: kv[0])]
    top_facilities = [
        {"facility_id": g.facility_id, "facility_name": g.facility_name, "total_gap_count": g.gap_count, "shift_count": 1}
        for g in gaps
    ]
    top_procedures = [
        {"required_procedure_code": g.required_procedure_code, "procedure_name": g.procedure_name, "total_gap_count": g.gap_count, "shift_count": 1}
        for g in gaps
    ]
    return StaffingSummaryResponse(
        by_risk_level=by_risk_level,
        daily_gap_count=daily_gap_count,
        top_facilities=top_facilities,
        top_procedures=top_procedures,
    )


def mock_shift_recommendations(shift_id: str) -> ShiftRecommendations:
    rec_ids = ["PROV-001", "PROV-002"]
    minis = [
        ProviderMini(provider_id="PROV-001", provider_name="Alex Morgan", specialty="Emergency Medicine", provider_status="ACTIVE"),
        ProviderMini(provider_id="PROV-002", provider_name="Jordan Lee", specialty="Surgery", provider_status="ACTIVE"),
    ]
    return ShiftRecommendations(shift_id=shift_id, recommended_provider_ids=rec_ids, recommended_providers=minis)


def mock_shift_prediction(shift_id: str) -> ShiftPredictionResponse:
    now = _now()
    return ShiftPredictionResponse(shift_id=shift_id, predicted_gap_prob=0.72, predicted_is_gap=1, scored_at=now)


def mock_credential_risk() -> list[CredentialRiskRow]:
    now = _now()
    return [
        CredentialRiskRow(
            event_id="EVT-PROV-001-LIC",
            provider_id="PROV-001",
            cred_type="STATE_MED_LICENSE",
            issued_at=now - timedelta(days=700),
            expires_at=now + timedelta(days=21),
            verified_at=now - timedelta(days=690),
            source_system="CRED_SYS_A",
            cred_status="ACTIVE",
            ingested_at=now - timedelta(hours=1),
            days_until_expiration=21,
            risk_bucket="15-30",
            last_built_at=now,
        ),
        CredentialRiskRow(
            event_id="EVT-PROV-002-ACLS",
            provider_id="PROV-002",
            cred_type="ACLS",
            issued_at=now - timedelta(days=400),
            expires_at=now + timedelta(days=10),
            verified_at=None,
            source_system="CRED_SYS_B",
            cred_status="PENDING_REVIEW",
            ingested_at=now - timedelta(hours=2),
            days_until_expiration=10,
            risk_bucket="0-14",
            last_built_at=now,
        ),
        CredentialRiskRow(
            event_id="EVT-PROV-003-LIC",
            provider_id="PROV-003",
            cred_type="STATE_MED_LICENSE",
            issued_at=now - timedelta(days=900),
            expires_at=now - timedelta(days=5),
            verified_at=now - timedelta(days=890),
            source_system="CRED_SYS_A",
            cred_status="EXPIRED",
            ingested_at=now - timedelta(hours=3),
            days_until_expiration=-5,
            risk_bucket="EXPIRED",
            last_built_at=now,
        ),
    ]


def mock_credential_risk_summary() -> CredentialRiskSummaryResponse:
    rows = mock_credential_risk()
    by_bucket = {}
    by_type = {}
    by_week = {}
    for r in rows:
        by_bucket[r.risk_bucket] = by_bucket.get(r.risk_bucket, 0) + 1
        by_type[r.cred_type] = by_type.get(r.cred_type, 0) + 1
        wk = (r.expires_at.date() - timedelta(days=r.expires_at.date().weekday()))
        by_week[wk] = by_week.get(wk, 0) + 1
    return CredentialRiskSummaryResponse(
        by_bucket=[CountByLabel(label=k, count=v) for k, v in by_bucket.items()],
        by_cred_type=[CountByLabel(label=k, count=v) for k, v in by_type.items()],
        expires_by_week=[DateCount(date=k, count=v) for k, v in sorted(by_week.items(), key=lambda kv: kv[0])],
    )


def mock_providers_summary() -> ProvidersSummaryResponse:
    providers = mock_providers()
    by_spec = {}
    for p in providers:
        by_spec[p.specialty] = by_spec.get(p.specialty, 0) + 1

    def min_days(p: Provider360) -> int:
        a = p.state_license_days_left if p.state_license_days_left is not None else 999999
        b = p.acls_days_left if p.acls_days_left is not None else 999999
        return min(a, b)

    funnel = {
        "<=14": sum(1 for p in providers if min_days(p) <= 14),
        "<=30": sum(1 for p in providers if min_days(p) <= 30),
        "<=90": sum(1 for p in providers if min_days(p) <= 90),
    }

    def readiness(p: Provider360) -> int:
        score = 0
        score += 1 if p.provider_status == "ACTIVE" else 0
        score += 1 if (p.state_license_days_left is not None and p.state_license_days_left >= 0) else 0
        score += 1 if (p.acls_days_left is not None and p.acls_days_left >= 0) else 0
        score += 1 if p.active_payer_count > 0 else 0
        score += 1 if p.active_privilege_count > 0 else 0
        return score

    hist = {}
    for p in providers:
        s = str(readiness(p))
        hist[s] = hist.get(s, 0) + 1

    return ProvidersSummaryResponse(
        by_specialty=[CountByLabel(label=k, count=v) for k, v in by_spec.items()],
        expiring_funnel=[CountByLabel(label=k, count=v) for k, v in funnel.items()],
        readiness_histogram=[CountByLabel(label=k, count=v) for k, v in sorted(hist.items(), key=lambda kv: int(kv[0]))],
    )


# ---- Closed-loop actions (local dev fallback) ----

_ACTIONS_STORE: dict[str, RiskAction] = {}


def _seed_actions_if_needed() -> None:
    if _ACTIONS_STORE:
        return
    now = _now()
    # Seed one SHIFT and one PROVIDER action that line up with mock IDs.
    a1 = RiskAction(
        action_id="ACT-001",
        entity_type="SHIFT",
        entity_id="SHIFT-001",
        facility_id="FAC-001",
        action_type="OUTREACH",
        status="OPEN",
        priority="HIGH",
        owner="staffing_coordinator",
        created_at=now - timedelta(hours=18),
        updated_at=now - timedelta(hours=2),
        resolved_at=None,
        notes="Outreach: confirm per-diem availability; consider cross-cover.",
        last_built_at=now,
    )
    a2 = RiskAction(
        action_id="ACT-002",
        entity_type="PROVIDER",
        entity_id="PROV-002",
        facility_id="FAC-002",
        action_type="CREDENTIAL_EXPEDITE",
        status="IN_PROGRESS",
        priority="HIGH",
        owner="med_staff_office",
        created_at=now - timedelta(days=2, hours=3),
        updated_at=now - timedelta(hours=6),
        resolved_at=None,
        notes="ACLS expiring soon; awaiting verification from source system.",
        last_built_at=now,
    )
    _ACTIONS_STORE[a1.action_id] = a1
    _ACTIONS_STORE[a2.action_id] = a2


def mock_actions_page(
    *,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    status: Optional[str] = None,
    action_type: Optional[str] = None,
    facility_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
):
    from models.common import PageResponse

    _seed_actions_if_needed()
    items = list(_ACTIONS_STORE.values())

    def ok(a: RiskAction) -> bool:
        if entity_type and a.entity_type != entity_type:
            return False
        if entity_id and a.entity_id != entity_id:
            return False
        if status and a.status != status:
            return False
        if action_type and a.action_type != action_type:
            return False
        if facility_id and a.facility_id != facility_id:
            return False
        return True

    filtered = [a for a in items if ok(a)]
    filtered.sort(key=lambda a: a.updated_at, reverse=True)
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    return PageResponse[RiskAction](items=filtered[start:end], total=total, page=page, page_size=page_size)


def mock_actions_create(payload: CreateRiskActionRequest) -> RiskAction:
    _seed_actions_if_needed()
    now = _now()
    action_id = f"ACT-{len(_ACTIONS_STORE) + 1:03d}"
    a = RiskAction(
        action_id=action_id,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        facility_id=payload.facility_id,
        action_type=payload.action_type,
        status="OPEN",
        priority=payload.priority,
        owner=payload.owner,
        created_at=now,
        updated_at=now,
        resolved_at=None,
        notes=payload.notes,
        last_built_at=now,
    )
    _ACTIONS_STORE[a.action_id] = a
    return a


def mock_actions_update(action_id: str, payload: UpdateRiskActionRequest) -> RiskAction:
    _seed_actions_if_needed()
    now = _now()
    a = _ACTIONS_STORE.get(action_id)
    if not a:
        # Create a placeholder so the UI can continue in local mode.
        a = RiskAction(
            action_id=action_id,
            entity_type="SHIFT",
            entity_id="SHIFT-001",
            facility_id="FAC-001",
            action_type="OUTREACH",
            status="OPEN",
            priority="MEDIUM",
            owner=None,
            created_at=now - timedelta(hours=1),
            updated_at=now - timedelta(hours=1),
            resolved_at=None,
            notes=None,
            last_built_at=now,
        )
        _ACTIONS_STORE[action_id] = a

    data = a.model_dump()
    if payload.status is not None:
        data["status"] = payload.status
        data["resolved_at"] = now if payload.status == "RESOLVED" else None
    if payload.priority is not None:
        data["priority"] = payload.priority
    if payload.owner is not None:
        data["owner"] = payload.owner
    if payload.notes is not None:
        data["notes"] = payload.notes
    data["updated_at"] = now
    data["last_built_at"] = now

    updated = RiskAction.model_validate(data)
    _ACTIONS_STORE[action_id] = updated
    return updated


# ---- Nurse Staffing Mock Data ----

def mock_units() -> list[Unit]:
    """Generate mock hospital units across facilities."""
    return [
        Unit(unit_id="UNIT-ICU-001", facility_id="FAC-001", facility_name="Manhattan General", unit_name="ICU Tower A", unit_type="ICU", bed_count=20, target_ratio=2.0),
        Unit(unit_id="UNIT-ICU-002", facility_id="FAC-002", facility_name="Brooklyn Community", unit_name="ICU West", unit_type="ICU", bed_count=16, target_ratio=2.0),
        Unit(unit_id="UNIT-MEDSURG-001", facility_id="FAC-001", facility_name="Manhattan General", unit_name="Med-Surg 3rd Floor", unit_type="MED_SURG", bed_count=40, target_ratio=5.0),
        Unit(unit_id="UNIT-MEDSURG-002", facility_id="FAC-002", facility_name="Brooklyn Community", unit_name="Med-Surg East", unit_type="MED_SURG", bed_count=32, target_ratio=5.0),
        Unit(unit_id="UNIT-TELE-001", facility_id="FAC-001", facility_name="Manhattan General", unit_name="Telemetry Unit", unit_type="TELEMETRY", bed_count=24, target_ratio=4.0),
        Unit(unit_id="UNIT-ED-001", facility_id="FAC-001", facility_name="Manhattan General", unit_name="Emergency Department", unit_type="ED", bed_count=30, target_ratio=4.0),
        Unit(unit_id="UNIT-ED-002", facility_id="FAC-002", facility_name="Brooklyn Community", unit_name="Emergency Room", unit_type="ED", bed_count=24, target_ratio=4.0),
        Unit(unit_id="UNIT-STEPDOWN-001", facility_id="FAC-001", facility_name="Manhattan General", unit_name="Step-Down Unit", unit_type="STEP_DOWN", bed_count=18, target_ratio=3.0),
        Unit(unit_id="UNIT-OR-001", facility_id="FAC-001", facility_name="Manhattan General", unit_name="Operating Rooms", unit_type="OR", bed_count=12, target_ratio=1.0),
        Unit(unit_id="UNIT-NICU-001", facility_id="FAC-003", facility_name="Queens Regional", unit_name="Neonatal ICU", unit_type="NICU", bed_count=24, target_ratio=2.0),
    ]


def mock_nurse_staffing_summary() -> list[NurseStaffingSummary]:
    """Generate daily staffing summary per unit with various statuses."""
    now = _now()
    today = date.today()
    units = mock_units()
    summaries = []

    # Staffing scenarios for demo variety
    scenarios = [
        # unit_id, census, assigned, internal, contract, agency, status
        ("UNIT-ICU-001", 18, 8, 5, 2, 1, "UNDERSTAFFED"),  # 18/2=9 needed, 8 assigned
        ("UNIT-ICU-002", 12, 6, 4, 1, 1, "OPTIMAL"),       # 12/2=6 needed, 6 assigned
        ("UNIT-MEDSURG-001", 30, 7, 4, 2, 1, "OVERSTAFFED"),  # 30/5=6 needed, 7 assigned
        ("UNIT-MEDSURG-002", 28, 4, 2, 1, 1, "UNDERSTAFFED"),  # 28/5=5.6~6 needed, 4 assigned
        ("UNIT-TELE-001", 20, 5, 3, 1, 1, "OPTIMAL"),      # 20/4=5 needed, 5 assigned
        ("UNIT-ED-001", 25, 5, 3, 1, 1, "UNDERSTAFFED"),   # 25/4=6.25~7 needed, 5 assigned
        ("UNIT-ED-002", 18, 5, 2, 2, 1, "OVERSTAFFED"),    # 18/4=4.5~5 needed, 5 assigned
        ("UNIT-STEPDOWN-001", 15, 4, 2, 1, 1, "UNDERSTAFFED"),  # 15/3=5 needed, 4 assigned
        ("UNIT-OR-001", 10, 10, 7, 2, 1, "OPTIMAL"),       # OR: 1:1 during cases
        ("UNIT-NICU-001", 20, 8, 5, 2, 1, "UNDERSTAFFED"),  # 20/2=10 needed, 8 assigned
    ]

    unit_map = {u.unit_id: u for u in units}

    for unit_id, census, assigned, internal, contract, agency, status in scenarios:
        u = unit_map.get(unit_id)
        if not u:
            continue
        nurses_required = max(1, int(census / u.target_ratio + 0.5))
        delta = assigned - nurses_required
        # Labor cost: internal $50/hr, contract $75/hr, agency $95/hr * 12-hour shifts
        labor_cost = (internal * 50 + contract * 75 + agency * 95) * 12

        summaries.append(NurseStaffingSummary(
            summary_date=today,
            unit_id=u.unit_id,
            facility_id=u.facility_id,
            facility_name=u.facility_name,
            unit_name=u.unit_name,
            unit_type=u.unit_type,
            bed_count=u.bed_count,
            current_census=census,
            target_ratio=u.target_ratio,
            nurses_required=nurses_required,
            nurses_assigned=assigned,
            nurses_internal=internal,
            nurses_contract=contract,
            nurses_agency=agency,
            staffing_delta=delta,
            staffing_status=status,
            labor_cost_daily=float(labor_cost),
            last_built_at=now,
        ))

    return summaries


def mock_nurse_staffing_kpis(facility_id: Optional[str] = None) -> NurseStaffingKpis:
    """Generate KPI summary for nurse staffing dashboard."""
    summaries = mock_nurse_staffing_summary()
    now = _now()

    if facility_id:
        summaries = [s for s in summaries if s.facility_id == facility_id]

    total_nurses = sum(s.nurses_assigned for s in summaries)
    total_contract_agency = sum(s.nurses_contract + s.nurses_agency for s in summaries)
    pct = (100.0 * total_contract_agency / total_nurses) if total_nurses > 0 else 0.0

    return NurseStaffingKpis(
        kpi_date=date.today(),
        total_nurses_on_shift=total_nurses,
        units_understaffed=sum(1 for s in summaries if s.staffing_status == "UNDERSTAFFED"),
        units_optimal=sum(1 for s in summaries if s.staffing_status == "OPTIMAL"),
        units_overstaffed=sum(1 for s in summaries if s.staffing_status == "OVERSTAFFED"),
        agency_contract_percentage=round(pct, 1),
        daily_labor_cost=sum(s.labor_cost_daily for s in summaries),
        credential_gaps_count=len(mock_credential_gaps()),
        last_built_at=now,
    )


def mock_credential_gaps() -> list[CredentialGapRow]:
    """Generate credential gaps - units where required certs are missing."""
    return [
        CredentialGapRow(
            unit_id="UNIT-ICU-001",
            facility_id="FAC-001",
            facility_name="Manhattan General",
            unit_name="ICU Tower A",
            unit_type="ICU",
            required_cred_type="ACLS",
            nurses_assigned=8,
            nurses_with_cert=6,
            nurses_missing_cert=2,
            gap_severity="HIGH",
            affected_nurse_ids=["NURSE-012", "NURSE-015"],
        ),
        CredentialGapRow(
            unit_id="UNIT-ICU-001",
            facility_id="FAC-001",
            facility_name="Manhattan General",
            unit_name="ICU Tower A",
            unit_type="ICU",
            required_cred_type="Critical Care Certification",
            nurses_assigned=8,
            nurses_with_cert=5,
            nurses_missing_cert=3,
            gap_severity="CRITICAL",
            affected_nurse_ids=["NURSE-012", "NURSE-015", "NURSE-018"],
        ),
        CredentialGapRow(
            unit_id="UNIT-ED-001",
            facility_id="FAC-001",
            facility_name="Manhattan General",
            unit_name="Emergency Department",
            unit_type="ED",
            required_cred_type="TNCC",
            nurses_assigned=5,
            nurses_with_cert=3,
            nurses_missing_cert=2,
            gap_severity="MEDIUM",
            affected_nurse_ids=["NURSE-022", "NURSE-025"],
        ),
        CredentialGapRow(
            unit_id="UNIT-NICU-001",
            facility_id="FAC-003",
            facility_name="Queens Regional",
            unit_name="Neonatal ICU",
            unit_type="NICU",
            required_cred_type="NRP",
            nurses_assigned=8,
            nurses_with_cert=6,
            nurses_missing_cert=2,
            gap_severity="HIGH",
            affected_nurse_ids=["NURSE-031", "NURSE-034"],
        ),
        CredentialGapRow(
            unit_id="UNIT-STEPDOWN-001",
            facility_id="FAC-001",
            facility_name="Manhattan General",
            unit_name="Step-Down Unit",
            unit_type="STEP_DOWN",
            required_cred_type="ACLS",
            nurses_assigned=4,
            nurses_with_cert=3,
            nurses_missing_cert=1,
            gap_severity="LOW",
            affected_nurse_ids=["NURSE-041"],
        ),
    ]


def mock_unit_detail(unit_id: str) -> UnitDetail:
    """Generate detailed view of a single unit."""
    now = _now()
    units = mock_units()
    summaries = mock_nurse_staffing_summary()

    unit = next((u for u in units if u.unit_id == unit_id), None)
    if not unit:
        # Return first unit as fallback
        unit = units[0]

    summary = next((s for s in summaries if s.unit_id == unit_id), None)
    if not summary:
        summary = summaries[0]

    # Generate mock assigned nurses
    assigned_nurses = []
    emp_types = ["INTERNAL"] * summary.nurses_internal + ["CONTRACT"] * summary.nurses_contract + ["AGENCY"] * summary.nurses_agency
    rates = {"INTERNAL": 50.0, "CONTRACT": 75.0, "AGENCY": 95.0}

    # Required certs by unit type
    required_certs = {
        "ICU": ["ACLS", "BLS", "Critical Care Certification"],
        "STEP_DOWN": ["ACLS", "BLS"],
        "MED_SURG": ["BLS"],
        "TELEMETRY": ["ACLS", "BLS"],
        "ED": ["ACLS", "BLS", "TNCC", "PALS"],
        "OR": ["BLS", "ACLS"],
        "L_AND_D": ["BLS", "NRP"],
        "PSYCH": ["BLS", "CPI"],
        "NICU": ["BLS", "NRP"],
        "PACU": ["ACLS", "BLS"],
    }

    unit_required = required_certs.get(unit.unit_type, ["BLS"])

    for i, emp_type in enumerate(emp_types):
        nurse_id = f"NURSE-{unit_id[-3:]}-{i+1:02d}"
        # Most nurses have all certs, some are missing one
        has_all = i < len(emp_types) - 2  # Last 2 nurses missing some certs
        certs = unit_required.copy() if has_all else unit_required[:-1]
        missing = [] if has_all else [unit_required[-1]]

        assigned_nurses.append(NurseAssignment(
            provider_id=nurse_id,
            provider_name=f"Nurse {chr(65 + i)} ({emp_type.title()})",
            employment_type=emp_type,
            hourly_rate=rates[emp_type],
            shift_start=now.replace(hour=7, minute=0, second=0, microsecond=0),
            shift_end=now.replace(hour=19, minute=0, second=0, microsecond=0),
            certifications=certs,
            missing_certifications=missing,
            is_fully_credentialed=has_all,
        ))

    return UnitDetail(
        unit=unit,
        summary=summary,
        assigned_nurses=assigned_nurses,
        required_certifications=unit_required,
    )


def mock_cost_breakdown(
    facility_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> CostBreakdown:
    """Generate labor cost breakdown by employment type."""
    summaries = mock_nurse_staffing_summary()

    if facility_id:
        summaries = [s for s in summaries if s.facility_id == facility_id]

    # Aggregate by employment type
    internal_count = sum(s.nurses_internal for s in summaries)
    contract_count = sum(s.nurses_contract for s in summaries)
    agency_count = sum(s.nurses_agency for s in summaries)
    total_nurses = internal_count + contract_count + agency_count

    # Hours and costs (12-hour shifts)
    internal_hours = internal_count * 12.0
    contract_hours = contract_count * 12.0
    agency_hours = agency_count * 12.0

    internal_cost = internal_hours * 50.0
    contract_cost = contract_hours * 75.0
    agency_cost = agency_hours * 95.0
    total_cost = internal_cost + contract_cost + agency_cost

    breakdown = [
        CostBreakdownItem(
            employment_type="INTERNAL",
            nurse_count=internal_count,
            total_hours=internal_hours,
            total_cost=internal_cost,
            avg_hourly_rate=50.0,
            percentage_of_total=round(100.0 * internal_cost / total_cost, 1) if total_cost > 0 else 0.0,
        ),
        CostBreakdownItem(
            employment_type="CONTRACT",
            nurse_count=contract_count,
            total_hours=contract_hours,
            total_cost=contract_cost,
            avg_hourly_rate=75.0,
            percentage_of_total=round(100.0 * contract_cost / total_cost, 1) if total_cost > 0 else 0.0,
        ),
        CostBreakdownItem(
            employment_type="AGENCY",
            nurse_count=agency_count,
            total_hours=agency_hours,
            total_cost=agency_cost,
            avg_hourly_rate=95.0,
            percentage_of_total=round(100.0 * agency_cost / total_cost, 1) if total_cost > 0 else 0.0,
        ),
    ]

    internal_pct = round(100.0 * internal_cost / total_cost, 1) if total_cost > 0 else 0.0
    outsourced_pct = round(100.0 - internal_pct, 1)

    facility_name = None
    if facility_id:
        fac_map = {"FAC-001": "Manhattan General", "FAC-002": "Brooklyn Community", "FAC-003": "Queens Regional"}
        facility_name = fac_map.get(facility_id)

    return CostBreakdown(
        facility_id=facility_id,
        facility_name=facility_name,
        start_date=start_date or date.today(),
        end_date=end_date or date.today(),
        total_labor_cost=total_cost,
        breakdown_by_type=breakdown,
        internal_percentage=internal_pct,
        outsourced_percentage=outsourced_pct,
    )

