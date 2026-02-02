from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class KpiSummaryDaily(BaseModel):
    kpi_date: date
    providers_total: int
    providers_pending: int
    providers_expiring_30d: int
    daily_revenue_at_risk_est: float
    last_built_at: datetime

