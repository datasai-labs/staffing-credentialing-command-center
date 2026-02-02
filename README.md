# Staffing + Credentialing Demo (Databricks App)

This repo contains a **single deployable** React + FastAPI app that reads from Unity Catalog Delta tables (gold layer) and renders dashboards + tables.

- Frontend: `app/frontend` (Vite + React + TypeScript + MUI)
- Backend: `app/backend` (FastAPI)

For local dev instructions, see [`app/README.md`](app/README.md).

## Deploy on Databricks Apps

This repo is prepped for Databricks Apps as a single deployable:

- `app.yaml` at repo root defines build + start commands
- `package.json` at repo root provides `npm run build` to compile the frontend
- `requirements.txt` at repo root installs backend Python deps

### Configure `app.yaml`

This repo ships with a **public-safe** `app.yaml` that contains placeholders only.

- For **private/internal** deployments: copy `app.yaml.private.example` → `app.yaml` and edit values as needed.
- For **public GitHub**: keep `app.yaml` with placeholders.

Edit (in your private copy):
- `resources.sql-warehouse`: set to your Databricks SQL Warehouse ID

Env vars:
- The app uses Databricks Apps ambient auth if available:
  - `DATABRICKS_HOST` + `DATABRICKS_TOKEN`
  - or OAuth M2M via `DATABRICKS_CLIENT_ID` / `DATABRICKS_CLIENT_SECRET`
- The SQL warehouse http path is injected by Apps via:
  - `DATABRICKS_SQL_WAREHOUSE_HTTP_PATH` (from `valueFrom: sql-warehouse`)

### Command (what Apps runs)

`app.yaml` runs:
- `npm run build` (builds `app/frontend/dist`)
- `uvicorn ... --port $DATABRICKS_APP_PORT` (FastAPI serves the SPA + API)

