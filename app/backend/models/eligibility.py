from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class EligibilityProviderExplain(BaseModel):
    provider_id: str
    provider_name: Optional[str] = None
    specialty: Optional[str] = None

    provider_status: Optional[str] = None
    home_facility_id: Optional[str] = None
    home_facility_name: Optional[str] = None

    state_license_status: Optional[str] = None
    state_license_days_left: Optional[int] = None
    acls_status: Optional[str] = None
    acls_days_left: Optional[int] = None
    active_privilege_count: Optional[int] = None
    active_payer_count: Optional[int] = None

    is_eligible: bool
    why_eligible: List[str] = Field(default_factory=list)
    why_not: List[str] = Field(default_factory=list)
    time_to_ready_days: Optional[int] = None


class ShiftEligibilityExplainResponse(BaseModel):
    shift_id: str
    recommended_provider_ids: List[str]
    providers: List[EligibilityProviderExplain]

