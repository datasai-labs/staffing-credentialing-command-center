from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from models.common import PageResponse
from models.credentials import CredentialRiskRow
from routes.v1._dbx import dbx_or_mock
from services import databricks
from services import mock_data
from services.queries import credential_risk_list_sql

router = APIRouter()


@router.get("/credential_risk", response_model=PageResponse[CredentialRiskRow])
def list_credential_risk(
    provider_id: Optional[str] = None,
    cred_type: Optional[str] = None,
    risk_bucket: Optional[str] = Query(default=None, description="Comma-separated: EXPIRED,0-14,15-30,31-90,>90"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    sort: Optional[str] = Query(default=None, description="field:asc|desc"),
):
    data_sql, count_sql, params = credential_risk_list_sql(
        provider_id=provider_id,
        cred_type=cred_type,
        risk_bucket=risk_bucket,
        page=page,
        page_size=page_size,
        sort=sort,
    )

    def _run():
        return databricks.fetch_paged(data_sql, count_sql, params)

    def _mock():
        all_items = mock_data.mock_credential_risk()
        items = all_items
        if provider_id:
            items = [r for r in items if r.provider_id == provider_id]
        if cred_type:
            items = [r for r in items if r.cred_type == cred_type]
        if risk_bucket:
            allowed = {x.strip() for x in risk_bucket.split(",") if x.strip()}
            items = [r for r in items if r.risk_bucket in allowed]
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return (items[start:end], total)

    rows, total = dbx_or_mock(lambda: databricks.with_retry(_run), _mock)
    items = [CredentialRiskRow.model_validate(r) for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size)

