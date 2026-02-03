# Staffing Command Center Demo

A React + FastAPI app for hospital staffing and credentialing management, deployed as a Databricks App.

**Fully Serverless:** This entire demo runs on serverless infrastructure—no clusters to configure. Notebooks run on serverless compute, and the app queries via serverless SQL Warehouse.

## Features

- Provider credentialing and compliance tracking
- Staffing gap analysis and shift recommendations
- Nurse staffing optimization with labor cost breakdown
- Census forecasting with auto-optimize recommendations

## Deployment

### Step 1: Set Up Data (Notebooks)

1. Upload all notebooks from `notebooks/` to your Databricks workspace
2. Run them in order:

| Notebook | Purpose |
|----------|---------|
| `01_seed_reference_data.ipynb` | Creates reference tables (facilities, units, credentials) |
| `02_generate_providers_and_credentials.ipynb` | Generates provider and credential data |
| `03_generate_shifts_and_assignments.ipynb` | Creates shifts and nurse assignments |
| `04_build_gold_views.ipynb` | Builds gold layer views for the app |
| `05_census_forecast_and_optimize.ipynb` | ML model for census forecasting & staffing optimization |

**Note:** Each notebook has widget parameters at the top. Default values work out of the box:
- `catalog`: `rtpa_catalog`
- `schema_ref/bronze/silver/gold`: `credentialing_*`

### Step 2: Deploy the App

#### Option A: Databricks CLI

```bash
# Authenticate
databricks auth login --host https://your-workspace.cloud.databricks.com

# Deploy the app
databricks apps deploy staffing-credentialing-demo --source-code-path .
```

#### Option B: Databricks Console

1. Go to **Compute > Apps** in your workspace
2. Click **Create App**
3. Upload this repository or connect via Git
4. The `app.yaml` configures the build and runtime

### Step 3: Configure `app.yaml`

Before deploying, update these values in `app.yaml`:

```yaml
env:
  - name: DATABRICKS_SERVER_HOSTNAME
    value: "your-workspace.cloud.databricks.com"  # Your workspace URL

resources:
  sql-warehouse: "your-warehouse-id"  # Your SQL Warehouse ID
```

Find your SQL Warehouse ID at: **SQL Warehouses > [warehouse] > Connection details**

## Local Development

See `app/README.md` for local development with mock data.

```bash
cd app
# Start backend
cd backend && pip install -r requirements.txt && ALLOW_MOCK_DATA=true uvicorn app:app --reload
# Start frontend (separate terminal)
cd frontend && npm install && npm run dev
```

## Project Structure

```
├── app.yaml              # Databricks App config
├── app/
│   ├── backend/          # FastAPI backend
│   └── frontend/         # React frontend
├── notebooks/            # Data pipeline notebooks (run these first)
└── requirements.txt      # Python dependencies
```
