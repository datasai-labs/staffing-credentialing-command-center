from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from models.common import PageResponse, parse_date
from models.staffing import StaffingGap
from models.worklists import CredentialExpiringRow, ProviderBlockersRow
from routes.v1._dbx import dbx_or_mock
from services import databricks, mock_data
from services.eligibility import Assumptions, explain_provider_readiness
from services.queries import (
    credential_expiring_worklist_sql,
    providers_blockers_worklist_sql,
    staffing_gaps_no_eligible_list_sql,
)

router = APIRouter()


@router.get("/worklists/shifts/no_eligible", response_model=PageResponse[StaffingGap])
def worklist_shifts_no_eligible(
    start_date: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    facility_id: Optional[str] = None,
    risk_level: Optional[str] = Query(default=None, description="Comma-separated: LOW,MEDIUM,HIGH"),
    procedure_code: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    sort: Optional[str] = Query(default=None, description="field:asc|desc"),
):
    sd: Optional[date] = parse_date(start_date) if start_date else None
    ed: Optional[date] = parse_date(end_date) if end_date else None
    data_sql, count_sql, params = staffing_gaps_no_eligible_list_sql(
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
        items = [r for r in mock_data.mock_staffing_gaps() if (r.eligible_provider_count or 0) == 0]
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
    parsed = [StaffingGap.model_validate(r) for r in rows]
    return PageResponse(items=parsed, total=total, page=page, page_size=page_size)


@router.get("/worklists/credentials/expiring", response_model=PageResponse[CredentialExpiringRow])
def worklist_credentials_expiring(
    provider_id: Optional[str] = None,
    specialty: Optional[str] = None,
    facility_id: Optional[str] = None,
    cred_type: Optional[str] = None,
    risk_bucket: Optional[str] = Query(default="0-14,15-30", description="Comma-separated buckets"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    sort: Optional[str] = Query(default="days_until_expiration:asc", description="field:asc|desc"),
):
    data_sql, count_sql, params = credential_expiring_worklist_sql(
        provider_id=provider_id,
        specialty=specialty,
        facility_id=facility_id,
        cred_type=cred_type,
        risk_bucket=risk_bucket,
        page=page,
        page_size=page_size,
        sort=sort,
    )

    def _run():
        return databricks.fetch_paged(data_sql, count_sql, params)

    def _mock():
        prov = {p.provider_id: p for p in mock_data.mock_providers()}
        items = []
        for r in mock_data.mock_credential_risk():
            if provider_id and r.provider_id != provider_id:
                continue
            if cred_type and r.cred_type != cred_type:
                continue
            if risk_bucket:
                allowed = {x.strip() for x in risk_bucket.split(",") if x.strip()}
                if r.risk_bucket not in allowed:
                    continue
            p = prov.get(r.provider_id)
            if specialty and p and p.specialty != specialty:
                continue
            if facility_id and p and p.home_facility_id != facility_id:
                continue
            row = CredentialExpiringRow(
                **r.model_dump(),
                provider_name=p.provider_name if p else None,
                specialty=p.specialty if p else None,
                home_facility_id=p.home_facility_id if p else None,
                home_facility_name=p.home_facility_name if p else None,
            )
            items.append(row)
        items.sort(key=lambda x: x.days_until_expiration)
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return (items[start:end], total)

    rows, total = dbx_or_mock(lambda: databricks.with_retry(_run), _mock)
    parsed = [CredentialExpiringRow.model_validate(r) for r in rows]
    return PageResponse(items=parsed, total=total, page=page, page_size=page_size)


@router.get("/worklists/providers/blockers", response_model=PageResponse[ProviderBlockersRow])
def worklist_providers_blockers(
    facility_id: Optional[str] = None,
    specialty: Optional[str] = None,
    blocker: Optional[str] = Query(default=None, description="LICENSE|ACLS|PRIVILEGE|PAYER"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    sort: Optional[str] = Query(default="last_built_at:desc", description="field:asc|desc"),
):
    data_sql, count_sql, params = providers_blockers_worklist_sql(
        facility_id=facility_id,
        specialty=specialty,
        blocker=blocker,
        page=page,
        page_size=page_size,
        sort=sort,
    )

    def _run():
        return databricks.fetch_paged(data_sql, count_sql, params)

    def _mock():
        items = [p for p in mock_data.mock_providers() if p.provider_status == "ACTIVE"]
        if facility_id:
            items = [p for p in items if p.home_facility_id == facility_id]
        if specialty:
            items = [p for p in items if p.specialty == specialty]
        # Ensure at least one blocker
        def is_blocked(p):
            if (p.state_license_days_left is not None and p.state_license_days_left < 0) or p.state_license_days_left is None:
                pass
            if (p.acls_days_left is not None and p.acls_days_left < 0) or p.acls_days_left is None:
                pass
            if (p.active_privilege_count or 0) == 0:
                pass
            if (p.active_payer_count or 0) == 0:
                pass
            return (
                (p.state_license_days_left is None or p.state_license_days_left < 0)
                or (p.acls_days_left is None or p.acls_days_left < 0)
                or (p.active_privilege_count or 0) == 0
                or (p.active_payer_count or 0) == 0
            )

        items = [p for p in items if is_blocked(p)]
        if blocker:
            b = blocker.upper().strip()
            if b == "LICENSE":
                items = [p for p in items if p.state_license_days_left is None or p.state_license_days_left < 0]
            elif b == "ACLS":
                items = [p for p in items if p.acls_days_left is None or p.acls_days_left < 0]
            elif b == "PRIVILEGE":
                items = [p for p in items if (p.active_privilege_count or 0) == 0]
            elif b == "PAYER":
                items = [p for p in items if (p.active_payer_count or 0) == 0]
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return (items[start:end], total)

    rows, total = dbx_or_mock(lambda: databricks.with_retry(_run), _mock)
    out: list[ProviderBlockersRow] = []
    for r in rows:
        if hasattr(r, "model_dump"):
            data = r.model_dump()
        else:
            data = dict(r)
        exp = explain_provider_readiness(data, assumptions=Assumptions.empty())
        blockers = []
        if exp.provider_status != "ACTIVE":
            blockers.append("STATUS")
        blockers.extend(["LICENSE" for x in exp.why_not if x.lower().startswith("license")])
        blockers.extend(["ACLS" for x in exp.why_not if x.lower().startswith("acls")])
        if any("privilege" in x.lower() for x in exp.why_not):
            blockers.append("PRIVILEGE")
        if any("payer" in x.lower() for x in exp.why_not):
            blockers.append("PAYER")
        blockers = list(dict.fromkeys(blockers))
        # Time-to-ready narrative
        ttr = exp.time_to_ready_days
        reason = exp.why_not[0] if exp.why_not else None
        out.append(
            ProviderBlockersRow(
                provider_id=data.get("provider_id"),
                provider_name=data.get("provider_name"),
                specialty=data.get("specialty"),
                provider_status=data.get("provider_status"),
                home_facility_id=data.get("home_facility_id"),
                home_facility_name=data.get("home_facility_name"),
                state_license_status=data.get("state_license_status"),
                state_license_days_left=data.get("state_license_days_left"),
                acls_status=data.get("acls_status"),
                acls_days_left=data.get("acls_days_left"),
                active_privilege_count=int(data.get("active_privilege_count") or 0),
                active_privilege_facility_count=int(data.get("active_privilege_facility_count") or 0),
                active_payer_count=int(data.get("active_payer_count") or 0),
                last_built_at=data.get("last_built_at"),
                blockers=blockers,
                time_to_ready_days=ttr,
                time_to_ready_reason=reason,
            )
        )
    return PageResponse(items=out, total=total, page=page, page_size=page_size)

