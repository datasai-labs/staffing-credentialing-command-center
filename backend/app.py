from __future__ import annotations

"""
Databricks Apps entrypoint:
`uvicorn backend.app:app ...`

We keep the real application code in `app/backend/` (per this repo's structure),
and expose it here by adding that directory to `sys.path`.
"""

import sys
from pathlib import Path

# Make `app/backend` importable as top-level modules (routes/, services/, settings.py, app.py, etc.)
BACKEND_DIR = Path(__file__).resolve().parents[1] / "app" / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Import the actual FastAPI instance from app/backend/app.py (module name: `app`)
import app as _backend_app_module  # type: ignore

app = _backend_app_module.app

