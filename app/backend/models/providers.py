from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


ProviderStatus = Literal["ACTIVE", "INACTIVE", "ON_LEAVE"]


class Provider360(BaseModel):
    provider_id: str
    provider_name: str
    specialty: str
    home_facility_id: str
    hired_at: date
    provider_status: ProviderStatus
    created_at: datetime

    home_facility_name: Optional[str] = None
    state_license_status: Optional[str] = None
    state_license_days_left: Optional[int] = None
    acls_status: Optional[str] = None
    acls_days_left: Optional[int] = None

    active_privilege_count: int = 0
    active_privilege_facility_count: int = 0
    active_payer_count: int = 0

    last_built_at: Optional[datetime] = None


class ProviderMini(BaseModel):
    provider_id: str
    provider_name: str
    specialty: Optional[str] = None
    provider_status: Optional[str] = None


class ProviderDetailResponse(BaseModel):
    provider: Provider360
    credential_risk_rows: list["CredentialRiskRow"] = Field(default_factory=list)


from .credentials import CredentialRiskRow  # noqa: E402  (type reuse, avoid duplication)

