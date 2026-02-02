from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


CredentialRiskBucket = Literal["EXPIRED", "0-14", "15-30", "31-90", ">90"]
ProviderBlocker = Literal["LICENSE", "ACLS", "PRIVILEGE", "PAYER", "STATUS"]


class CredentialExpiringRow(BaseModel):
    # Credential risk fields (from gold.credential_risk)
    event_id: str
    provider_id: str
    cred_type: str
    issued_at: datetime
    expires_at: datetime
    verified_at: Optional[datetime] = None
    source_system: str
    cred_status: str
    ingested_at: datetime
    days_until_expiration: int
    risk_bucket: str
    last_built_at: Optional[datetime] = None

    # Provider enrichment (from gold.provider_360_flat)
    provider_name: Optional[str] = None
    specialty: Optional[str] = None
    home_facility_id: Optional[str] = None
    home_facility_name: Optional[str] = None


class ProviderBlockersRow(BaseModel):
    provider_id: str
    provider_name: str
    specialty: str
    provider_status: str
    home_facility_id: str

    home_facility_name: Optional[str] = None
    state_license_status: Optional[str] = None
    state_license_days_left: Optional[int] = None
    acls_status: Optional[str] = None
    acls_days_left: Optional[int] = None
    active_privilege_count: int = 0
    active_privilege_facility_count: int = 0
    active_payer_count: int = 0
    last_built_at: Optional[datetime] = None

    blockers: List[ProviderBlocker] = Field(default_factory=list)
    time_to_ready_days: Optional[int] = None
    time_to_ready_reason: Optional[str] = None

