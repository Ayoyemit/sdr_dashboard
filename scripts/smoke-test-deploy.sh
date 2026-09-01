#!/usr/bin/env bash
# Smoke-test API after deploy (local or Railway).
# Usage:
#   ./scripts/smoke-test-deploy.sh
#   API_BASE=https://your-api.up.railway.app ./scripts/smoke-test-deploy.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_BASE="${API_BASE:-http://127.0.0.1:8000}"

echo "== Local pytest =="
cd "$ROOT/sdr-api"
PYTHONPATH=../sim pytest tests/test_api.py::test_meta_counties tests/test_api.py::test_run_status_quo_quick tests/test_api.py::test_run_kisii_quick -m slow -q

echo "== HTTP smoke ($API_BASE) =="
if ! curl -q -sS --connect-timeout 2 "$API_BASE/health" >/dev/null 2>&1; then
  echo "SKIP HTTP checks (API not reachable at $API_BASE). Redeploy on Railway, then run:"
  echo "  API_BASE=https://your-api.up.railway.app ./scripts/smoke-test-deploy.sh"
  exit 0
fi
for county in kakamega kisii; do
  payload=$(cat <<EOF
{"name":"Smoke $county","county":"$county","run":{"mode":"quick","implementation_years":1,"maintenance_years":0}}
EOF
)
  code=$(curl -q -sS -o /tmp/sdr-smoke.json -w "%{http_code}" \
    -X POST "$API_BASE/api/v1/scenarios/run" \
    -H "Content-Type: application/json" \
    -d "$payload")
  if [[ "$code" != "200" ]]; then
    echo "FAIL $county HTTP $code"
    cat /tmp/sdr-smoke.json
    exit 1
  fi
  status=$(python3 -c "import json; print(json.load(open('/tmp/sdr-smoke.json'))['status'])")
  echo "OK $county status=$status"
done

echo "All smoke checks passed."
