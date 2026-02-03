from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# Employment types
EmploymentType = Literal["INTERNAL", "CONTRACT", "AGENCY"]

# Unit types for hospital units
UnitType = Literal["ICU", "STEP_DOWN", "MED_SURG", "TELEMETRY", "ED", "OR", "L_AND_D", "PSYCH", "NICU", "PACU"]

# Staffing status
StaffingStatus = Literal["UNDERSTAFFED", "OPTIMAL", "OVERSTAFFED"]


class Unit(BaseModel):
    """Reference data for hospital units."""
    unit_id: str
    facility_id: str
    facility_name: Optional[str] = None
    unit_name: str
    unit_type: UnitType
    bed_count: int = Field(ge=0)
    target_ratio: float = Field(ge=0, description="Target nurse-to-patient ratio (patients per nurse)")


class UnitCertification(BaseModel):
    """Certification requirements by unit type."""
    unit_type: UnitType
    cred_type: str
    is_required: bool = True


class NurseStaffingSummary(BaseModel):
    """Daily staffing summary per unit."""
    summary_date: date
    unit_id: str
    facility_id: str
    facility_name: Optional[str] = None
    unit_name: str
    unit_type: UnitType
    bed_count: int
    current_census: int = Field(ge=0, description="Current patient count in unit")
    target_ratio: float = Field(ge=0, description="Required nurse-to-patient ratio")
    nurses_required: int = Field(ge=0, description="Nurses needed based on census and ratio")
    nurses_assigned: int = Field(ge=0, description="Total nurses assigned")
    nurses_internal: int = Field(ge=0, description="Internal/FTE nurses")
    nurses_contract: int = Field(ge=0, description="Contract nurses")
    nurses_agency: int = Field(ge=0, description="Agency/travel nurses")
    staffing_delta: int = Field(description="assigned - required (positive = overstaffed)")
    staffing_status: StaffingStatus
    labor_cost_daily: float = Field(ge=0, description="Estimated daily labor cost")
    last_built_at: Optional[datetime] = None


class NurseAssignment(BaseModel):
    """A nurse assigned to a unit."""
    provider_id: str
    provider_name: str
    employment_type: EmploymentType
    hourly_rate: float = Field(ge=0)
    shift_start: datetime
    shift_end: datetime
    certifications: list[str] = Field(default_factory=list, description="List of active certifications")
    missing_certifications: list[str] = Field(default_factory=list, description="Required certs not held")
    is_fully_credentialed: bool = Field(description="Has all required certs for unit")


class UnitDetail(BaseModel):
    """Detailed view of a single unit with assigned nurses."""
    unit: Unit
    summary: NurseStaffingSummary
    assigned_nurses: list[NurseAssignment] = Field(default_factory=list)
    required_certifications: list[str] = Field(default_factory=list)


class CredentialGapRow(BaseModel):
    """A unit where required certifications are missing among assigned nurses."""
    unit_id: str
    facility_id: str
    facility_name: Optional[str] = None
    unit_name: str
    unit_type: UnitType
    required_cred_type: str
    nurses_assigned: int = Field(ge=0)
    nurses_with_cert: int = Field(ge=0)
    nurses_missing_cert: int = Field(ge=0)
    gap_severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    affected_nurse_ids: list[str] = Field(default_factory=list)


class CostBreakdownItem(BaseModel):
    """Cost breakdown by employment type."""
    employment_type: EmploymentType
    nurse_count: int = Field(ge=0)
    total_hours: float = Field(ge=0)
    total_cost: float = Field(ge=0)
    avg_hourly_rate: float = Field(ge=0)
    percentage_of_total: float = Field(ge=0, le=100)


class CostBreakdown(BaseModel):
    """Labor cost breakdown for a facility or date range."""
    facility_id: Optional[str] = None
    facility_name: Optional[str] = None
    start_date: date
    end_date: date
    total_labor_cost: float = Field(ge=0)
    breakdown_by_type: list[CostBreakdownItem] = Field(default_factory=list)
    internal_percentage: float = Field(ge=0, le=100)
    outsourced_percentage: float = Field(ge=0, le=100, description="Contract + Agency percentage")


class NurseStaffingKpis(BaseModel):
    """KPI summary for nurse staffing dashboard."""
    kpi_date: date
    total_nurses_on_shift: int = Field(ge=0)
    units_understaffed: int = Field(ge=0)
    units_optimal: int = Field(ge=0)
    units_overstaffed: int = Field(ge=0)
    agency_contract_percentage: float = Field(ge=0, le=100)
    daily_labor_cost: float = Field(ge=0)
    credential_gaps_count: int = Field(ge=0)
    last_built_at: Optional[datetime] = None


class CensusForecast(BaseModel):
    """Predicted census for a unit on a future date."""
    forecast_date: date
    unit_id: str
    facility_id: str
    facility_name: Optional[str] = None
    unit_name: str
    unit_type: str
    bed_count: int
    predicted_census: int
    predicted_occupancy_pct: float
    nurses_required: int
    confidence_pct: int
    is_weekend: bool = False


class StaffingOptimization(BaseModel):
    """Auto-optimized staffing recommendation."""
    forecast_date: date
    unit_id: str
    facility_id: str
    facility_name: Optional[str] = None
    unit_name: str
    unit_type: str
    predicted_census: int
    nurses_required: int
    current_staffed: int
    staffing_delta: int
    opt_internal: int
    opt_contract: int
    opt_agency: int
    opt_total: int
    opt_daily_cost: float
    internal_pct: float
    outsourced_pct: float
    current_daily_cost: float
    cost_savings: float
    action: str
    priority: Literal["LOW", "MEDIUM", "HIGH"]
    confidence_pct: int


class OptimizationSummary(BaseModel):
    """7-day optimization outlook summary."""
    total_nurses_needed: int
    total_optimized_cost: float
    total_potential_savings: float
    units_needing_attention: int
    high_priority_count: int
    forecast_days: int
