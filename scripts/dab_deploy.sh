#!/usr/bin/env bash
set -euo pipefail

# Deploy bundle resources (job + synced files).
databricks bundle deploy -t "${1:-dev}"

echo
echo "Bundle deployed."
echo "Next:"
echo "- Run notebooks pipeline: databricks bundle run -t ${1:-dev} build_demo_tables"
echo "- Deploy Databricks App separately (Apps support in DAB varies by CLI/version):"
echo "  databricks apps deploy <app_name> --source-code-path <workspace_path>"

