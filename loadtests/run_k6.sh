#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export MSYS_NO_PATHCONV=1

to_win() {
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -w "$1" | sed 's|\\|/|g'
  else
    echo "$1"
  fi
}

K6_DIR="$(to_win "$ROOT/loadtests/k6")"
FIX_DIR="$(to_win "$ROOT/loadtests/fixtures")"
RES_DIR="$(to_win "$ROOT/loadtests/results")"
BASE_URL="${BASE_URL:-http://host.docker.internal:8000}"

mkdir -p "$ROOT/loadtests/fixtures" "$ROOT/loadtests/results"
"$ROOT/backend/.venv/Scripts/python.exe" "$ROOT/loadtests/scripts/generate_fixtures.py" >/dev/null

echo "base url: $BASE_URL"
for script in smoke load_all_apis export_test upload_stress upload_over_limit upload_max; do
  echo ""
  echo "=== k6 $script ==="
  docker run --rm \
    -v "$K6_DIR:/scripts" \
    -v "$FIX_DIR:/scripts/fixtures" \
    -v "$RES_DIR:/results" \
    -e BASE_URL="$BASE_URL" \
    grafana/k6 run "/scripts/$script.js" "--summary-export=/results/$script.json" \
    || echo "[warn] $script reported failed thresholds or checks"
done
echo ""
echo "summary exports -> $ROOT/loadtests/results"
