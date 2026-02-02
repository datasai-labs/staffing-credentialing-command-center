from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CountByLabel(BaseModel):
    label: str
    count: int = Field(ge=0)


class DateCount(BaseModel):
    date: date
    count: int = Field(ge=0)


class DateValue(BaseModel):
    date: date
    value: float


class KpiTrendPoint(BaseModel):
    kpi_date: date
    providers_pending: int
    providers_expiring_30d: int
    daily_revenue_at_risk_est: float


class KpiTrendResponse(BaseModel):
    days: int
    points: List[KpiTrendPoint]


class StaffingSummaryResponse(BaseModel):
    by_risk_level: List[CountByLabel]
    daily_gap_count: List[DateValue]
    top_facilities: List[dict]
    top_procedures: List[dict]


class CredentialRiskSummaryResponse(BaseModel):
    by_bucket: List[CountByLabel]
    by_cred_type: List[CountByLabel]
    expires_by_week: List[DateCount]


class ProvidersSummaryResponse(BaseModel):
    by_specialty: List[CountByLabel]
    expiring_funnel: List[CountByLabel]
    readiness_histogram: List[CountByLabel]


class ShiftPredictionResponse(BaseModel):
    shift_id: str
    predicted_gap_prob: Optional[float] = None
    predicted_is_gap: Optional[int] = None
    scored_at: Optional[datetime] = None

