from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]


class StaffingGap(BaseModel):
    shift_id: str
    facility_id: str
    facility_name: Optional[str] = None
    start_ts: datetime
    end_ts: datetime
    required_procedure_code: str
    procedure_name: Optional[str] = None
    required_count: int
    assigned_count: int
    eligible_provider_count: int
    gap_count: int
    risk_reason: str
    risk_level: str
    last_built_at: Optional[datetime] = None


class ShiftRecommendations(BaseModel):
    shift_id: str
    recommended_provider_ids: List[str]
    recommended_providers: Optional[List["ProviderMini"]] = None


from .providers import ProviderMini  # noqa: E402  (avoid circular import)

