#!/bin/sh
set -eu

echo "[startup] Databricks Apps bootstrap starting..."

PORT="${DATABRICKS_APP_PORT:-8000}"
echo "[startup] Using port: ${PORT}"

pick_python() {
  for c in python python3.10 python3; do
    if command -v "$c" >/dev/null 2>&1; then
      echo "$c"
      return 0
    fi
  done
  return 1
}

PY="$(pick_python || true)"
if [ -z "${PY}" ]; then
  echo "[startup][error] No python interpreter found on PATH (tried: python, python3.10, python3)" >&2
  exit 1
fi
echo "[startup] Using python: ${PY}"

have_pip_module() {
  "${PY}" -c "import pip" >/dev/null 2>&1
}

have_pip_cmd() {
  command -v pip >/dev/null 2>&1 || command -v pip3 >/dev/null 2>&1
}

install_requirements() {
  if have_pip_module; then
    echo "[startup] Installing requirements via: ${PY} -m pip"
    "${PY}" -m pip install --upgrade pip >/dev/null 2>&1 || true
    "${PY}" -m pip install -r requirements.txt
    return 0
  fi

  if command -v pip >/dev/null 2>&1; then
    echo "[startup] Installing requirements via: pip"
    pip install -r requirements.txt
    return 0
  fi

  if command -v pip3 >/dev/null 2>&1; then
    echo "[startup] Installing requirements via: pip3"
    pip3 install -r requirements.txt
    return 0
  fi

  echo "[startup][error] pip not available (no pip module, no pip/pip3 command). Cannot install requirements." >&2
  exit 1
}

# Ensure uvicorn is importable for the chosen python
if "${PY}" -c "import uvicorn" >/dev/null 2>&1; then
  echo "[startup] uvicorn import OK"
else
  echo "[startup] uvicorn not importable; installing Python requirements..."
  install_requirements
fi

echo "[startup] Starting FastAPI..."
cd app/backend
exec "${PY}" -m uvicorn app:app --host 0.0.0.0 --port "${PORT}" --lifespan off

