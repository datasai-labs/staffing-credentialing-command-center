# Staffing + Credentialing Demo App

## What this demo shows (use case)

This is a **staffing + credentialing “command center”** demo for a health system:

- **Consolidates operational risk signals** from multiple domains into one view:
  - Staffing coverage gaps (unfilled/underfilled shifts)
  - Credential expiration risk (license/ACLS, etc.)
  - Provider readiness context (facility, specialty, privileges)
  - Closed-loop “risk mitigation actions” tied to a **SHIFT** or a **PROVIDER**
- **One front door for operations**: dashboards + filterable tables + drill-down, backed by Unity Catalog gold tables produced by the notebooks in `notebooks/`.

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

## Deploy with Databricks Asset Bundles (DAB)

This repo includes a root `databricks.yml` bundle that:
- Syncs the repo to a workspace path
- Creates a Job `build_demo_tables` with tasks that run notebooks 01–05 in order
- Passes notebook parameters (`catalog`, schemas, `seed`, etc.) via widgets

### Prereqs
- Databricks CLI configured (`databricks auth login` or env-based auth)
- Update `node_type_id` (and optionally `spark_version`) in `databricks.yml` for your workspace/cloud

### Deploy + run the notebook pipeline

```bash
# Deploy bundle resources (sync + create job)
databricks bundle deploy -t dev

# Run the workflow/job (executes notebooks 01–05)
databricks bundle run -t dev build_demo_tables
```

### Deploy the app (after tables exist)

Databricks Apps deployment is handled via `app.yaml` (outside the DAB job).
Once the job has created the gold tables, deploy the app using Databricks Apps (UI/CLI) pointing at this repo.

