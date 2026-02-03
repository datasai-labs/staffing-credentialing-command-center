# Staffing Command Center Demo App

**Staffing Command Center** for a health system:

- **Consolidates operational risk signals** from multiple domains into one view:
  - Staffing coverage gaps (unfilled/underfilled shifts)
  - Credential expiration risk (license/ACLS, etc.)
  - Provider readiness context (facility, specialty, privileges)
  - Closed-loop “risk mitigation actions” tied to a **SHIFT** or a **PROVIDER**
- **One front door for operations**: dashboards + filterable tables + drill-down, backed by Unity Catalog gold tables produced by the notebooks in `notebooks/`.

## Repo map (frontend + backend)

### Backend (FastAPI)
- **Entrypoint**: `app/backend/app.py`
  - mounts versioned routes under `/api/v1/*`
  - serves the built SPA from `app/frontend/dist` (single deployable)
  - adds `x-request-id` middleware and a global exception handler
- **Routing**: `app/backend/routes/v1/*` (registered in `app/backend/routes/v1/__init__.py`)
- **Data access layer**: `app/backend/services/databricks.py`
  - Databricks SQL via `databricks-sql-connector` using **named parameters** (`:param`)
  - retry helper for transient failures
- **SQL builder / allow-listed sorting**: `app/backend/services/queries.py`
- **Mock mode**: `ALLOW_MOCK_DATA` (defaults on in dev/local); mock generators in `app/backend/services/mock_data.py`

### Frontend (Vite + React)
- **Entrypoint**: `app/frontend/src/main.tsx`
  - React Query for server-state caching/retries
  - React Router for navigation
  - Zod validates API responses at runtime
- **Routes/pages**: `app/frontend/src/app/routes.tsx`
  - `/` Overview
  - `/staffing` Staffing gaps
  - `/providers` Provider directory
  - `/providers/:id` Provider detail
  - `/credentials` Credential risk
- **API client + hooks**: `app/frontend/src/api/*`
  - `client.ts` (fetch wrappers)
  - `hooks.ts` (React Query hooks)
  - `types.ts` (Zod schemas + TS types)
- **Shared UI**: `app/frontend/src/components/*`
  - `DataTable` (server paging/sorting + CSV export)
  - `FilterBar`
  - `States` (loading/empty/error)
  - `ActionsPanel` (closed-loop mitigation actions)

## API + data contract

This app is designed to evolve by adding **derived views and app-layer computation** without renaming fields or requiring new columns in existing gold tables.

### Existing API surface (used by current UI)
- `GET /api/v1/healthcheck`
- `GET /api/v1/healthcheck/databricks`
- `GET /api/v1/kpis?as_of_date=YYYY-MM-DD`
- `GET /api/v1/kpis/trend?days=30`
- `GET /api/v1/providers?q&specialty&status&expiring_within_days&page&page_size&sort`
- `GET /api/v1/providers/summary?specialty&status&expiring_within_days`
- `GET /api/v1/providers/{provider_id}`
- `GET /api/v1/staffing_gaps?start_date&end_date&facility_id&risk_level&procedure_code&page&page_size&sort`
- `GET /api/v1/staffing_gaps/summary?start_date&end_date&facility_id&risk_level&procedure_code`
- `GET /api/v1/shifts/{shift_id}/recommendations?include_providers=true`
- `GET /api/v1/shifts/{shift_id}/prediction`
- `GET /api/v1/credential_risk?provider_id&cred_type&risk_bucket&page&page_size&sort`
- `GET /api/v1/credential_risk/summary?cred_type&risk_bucket`
- `GET /api/v1/actions?entity_type&entity_id&status&action_type&facility_id&page&page_size&sort`
- `GET /api/v1/actions/summary?facility_id`
- `POST /api/v1/actions`
- `PATCH /api/v1/actions/{action_id}`

### Gold tables queried by the backend today (no renames)
- `gold.provider_360_flat`
- `gold.staffing_gaps`
- `gold.shift_recommendations`
- `gold.credential_risk`
- `gold.kpi_summary_daily`
- `gold.shift_gap_predictions`
- `gold.risk_actions` (also used for INSERT/UPDATE)

### Fields the UI currently relies on (examples)
- **Provider360**: `provider_id, provider_name, specialty, home_facility_id, home_facility_name, hired_at, provider_status, created_at, state_license_status, state_license_days_left, acls_status, acls_days_left, active_privilege_count, active_privilege_facility_count, active_payer_count`
- **StaffingGap**: `shift_id, facility_id, facility_name, start_ts, end_ts, required_procedure_code, procedure_name, required_count, assigned_count, eligible_provider_count, gap_count, risk_level, risk_reason`
- **CredentialRiskRow**: `event_id, provider_id, cred_type, issued_at, expires_at, verified_at, source_system, cred_status, ingested_at, days_until_expiration, risk_bucket`
- **ShiftPredictionResponse**: `shift_id, predicted_gap_prob, predicted_is_gap, scored_at`
- **KpiSummaryDaily**: `kpi_date, providers_total, providers_pending, providers_expiring_30d, daily_revenue_at_risk_est`
- **RiskAction**: `action_id, entity_type, entity_id, facility_id, action_type, status, priority, owner, created_at, updated_at, resolved_at, notes`

## What gets deployed (resources + UI frameworks)

### UI / frontend
- **React + TypeScript + Vite**
- **MUI** for consistent UI components + **MUI DataGrid** for tables
- **TanStack Query** for data fetching/caching/retries
- **Zod** for runtime validation of API responses
- **Recharts** for charts

### Backend
- **FastAPI (Python)** serving versioned endpoints under `/api/v1/*`
- Databricks SQL access via **`databricks-sql-connector`** (PAT or OAuth M2M)
- Optional local preview via **mock data** (controlled by `ALLOW_MOCK_DATA`)

### Data + notebooks
The DAB workflow runs notebooks **01 → 05** to create/update:
- Reference tables (ref)
- Bronze raw tables
- Silver “current state” tables
- Gold analytics tables used by the app (provider 360, staffing gaps, credential risk, KPIs, recommendations, actions)