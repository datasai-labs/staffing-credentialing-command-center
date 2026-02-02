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

