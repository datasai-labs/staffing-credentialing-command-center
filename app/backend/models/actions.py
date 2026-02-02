from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


ActionEntityType = Literal["SHIFT", "PROVIDER"]
ActionStatus = Literal["OPEN", "IN_PROGRESS", "RESOLVED"]
ActionPriority = Literal["LOW", "MEDIUM", "HIGH"]
ActionType = Literal["OUTREACH", "CREDENTIAL_EXPEDITE", "PRIVILEGE_REQUEST", "PAYER_ENROLLMENT_FOLLOWUP"]


class RiskAction(BaseModel):
    action_id: str
    entity_type: ActionEntityType
    entity_id: str
    facility_id: Optional[str] = None

    action_type: ActionType
    status: ActionStatus
    priority: ActionPriority = "MEDIUM"
    owner: Optional[str] = None

    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    notes: Optional[str] = None
    last_built_at: Optional[datetime] = None


class CreateRiskActionRequest(BaseModel):
    entity_type: ActionEntityType
    entity_id: str
    facility_id: Optional[str] = None

    action_type: ActionType
    priority: ActionPriority = "MEDIUM"
    owner: Optional[str] = None
    notes: Optional[str] = None


class UpdateRiskActionRequest(BaseModel):
    status: Optional[ActionStatus] = None
    priority: Optional[ActionPriority] = None
    owner: Optional[str] = None
    notes: Optional[str] = None


class ActionsSummary(BaseModel):
    open_count: int = Field(ge=0)
    in_progress_count: int = Field(ge=0)
    resolved_count: int = Field(ge=0)
    median_time_to_resolve_hours: Optional[float] = None

