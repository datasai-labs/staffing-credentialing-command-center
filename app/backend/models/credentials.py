from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CredentialRiskRow(BaseModel):
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

