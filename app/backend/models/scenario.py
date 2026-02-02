from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ScenarioAssumptions(BaseModel):
    fix_acls_for_provider_ids: List[str] = Field(default_factory=list)
    fix_license_for_provider_ids: List[str] = Field(default_factory=list)
    assume_payer_for_provider_ids: List[str] = Field(default_factory=list)
    assume_privilege_for_provider_ids: List[str] = Field(default_factory=list)


class ScenarioCoverageRequest(BaseModel):
    shift_ids: List[str] = Field(min_length=1, max_length=200)
    assumptions: ScenarioAssumptions = Field(default_factory=ScenarioAssumptions)


class ScenarioShiftResult(BaseModel):
    shift_id: str
    baseline_coverable: bool
    scenario_coverable: bool
    delta_coverable: bool
    # Best-effort explanation for demo narrative
    baseline_best_provider_id: Optional[str] = None
    scenario_best_provider_id: Optional[str] = None
    scenario_changes: List[str] = Field(default_factory=list)


class ScenarioCoverageResponse(BaseModel):
    shift_count: int
    baseline_coverable_count: int
    scenario_coverable_count: int
    delta_coverable_count: int
    results: List[ScenarioShiftResult]

