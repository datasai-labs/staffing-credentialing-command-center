from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from models.common import PageResponse
from models.credentials import CredentialRiskRow
from models.providers import Provider360, ProviderDetailResponse
from routes.v1._dbx import dbx_or_mock
from services import databricks
from services import mock_data
from services.queries import (
    credential_risk_list_sql,
    provider_detail_sql,
    providers_list_sql,
)

router = APIRouter()


@router.get("/providers", response_model=PageResponse[Provider360])
def list_providers(
    q: Optional[str] = None,
    specialty: Optional[str] = None,
    status: Optional[str] = None,
    expiring_within_days: Optional[int] = Query(default=None, ge=0, le=3650),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    sort: Optional[str] = Query(default=None, description="field:asc|desc"),
):
    data_sql, count_sql, params = providers_list_sql(
        q=q,
        specialty=specialty,
        status=status,
        expiring_within_days=expiring_within_days,
        page=page,
        page_size=page_size,
        sort=sort,
    )

    def _run():
        return databricks.fetch_paged(data_sql, count_sql, params)

    def _mock():
        all_items = mock_data.mock_providers()
        items = all_items
        if q:
            ql = q.lower()
            items = [p for p in items if ql in p.provider_id.lower() or ql in p.provider_name.lower()]
        if specialty:
            items = [p for p in items if p.specialty == specialty]
        if status:
            items = [p for p in items if p.provider_status == status]
        if expiring_within_days is not None:
            items = [
                p
                for p in items
                if (p.state_license_days_left is not None and p.state_license_days_left <= expiring_within_days)
                or (p.acls_days_left is not None and p.acls_days_left <= expiring_within_days)
            ]
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return (items[start:end], total)

    rows, total = dbx_or_mock(lambda: databricks.with_retry(_run), _mock)
    items = [Provider360.model_validate(r) for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/providers/{provider_id}", response_model=ProviderDetailResponse)
def get_provider(provider_id: str):
    sql_text, params = provider_detail_sql(provider_id)

    def _run():
        rows = databricks.fetch_all(sql_text, params).rows
        return rows[0] if rows else None

    row = dbx_or_mock(lambda: databricks.with_retry(_run), lambda: mock_data.mock_provider_detail(provider_id))
    if isinstance(row, ProviderDetailResponse):
        return row
    if not row:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider = Provider360.model_validate(row)

    # Optional: include recent credential risk rows for this provider
    risk_data_sql, risk_count_sql, risk_params = credential_risk_list_sql(
        provider_id=provider_id,
        cred_type=None,
        risk_bucket=None,
        page=1,
        page_size=50,
        sort="days_until_expiration:asc",
    )

    def _run_risk():
        return databricks.fetch_paged(risk_data_sql, risk_count_sql, risk_params)

    risk_rows, _total = dbx_or_mock(
        lambda: databricks.with_retry(_run_risk),
        lambda: (mock_data.mock_provider_detail(provider_id).credential_risk_rows, 0),
    )
    risk_items = [CredentialRiskRow.model_validate(r) for r in risk_rows]
    return ProviderDetailResponse(provider=provider, credential_risk_rows=risk_items)

