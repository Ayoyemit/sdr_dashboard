#!/usr/bin/env bash
# Sync Python model files from Poppy's sdr-dashboard-deploy repo into sim/.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if ! git remote | grep -q '^deploy$'; then
  git remote add deploy https://github.com/Poppyandnucky/sdr-dashboard-deploy.git
fi
git fetch deploy main
PY_FILES=(
  ANC_LB_effect_slider.py
  LB_effect.py
  global_func.py
  intrapartum.py
  model_run.py
  mortality.py
  parameter_loader.py
  parameter_test.py
  parameters.py
  debug_report.py
)
for f in "${PY_FILES[@]}"; do
  if git show "deploy/main:$f" >/dev/null 2>&1; then
    git show "deploy/main:$f" > "sim/$f"
    echo "synced sim/$f"
  fi
done
if git show "deploy/main:data/SDR Parameters.xlsx" >/dev/null 2>&1; then
  git show "deploy/main:data/SDR Parameters.xlsx" > "sim/SDR Parameters.xlsx"
  echo "synced sim/SDR Parameters.xlsx"
fi
# Keep bundled workbook path (deploy repo defaults to Poppy's OneDrive).
python3 <<'PY'
from pathlib import Path
p = Path("sim/parameter_loader.py")
text = p.read_text()
needle = 'WORKBOOK_PATH: Path = Path(os.environ.get('
if needle in text:
    bundled = '''# ---------------------------------------------------------------------------
# Module-level workbook path and county default.
# Override at runtime with SDR_PARAMS_PATH, e.g.:
#   export SDR_PARAMS_PATH=/app/sim/SDR Parameters.xlsx
# Default prefers bundled sim/SDR Parameters.xlsx, then Poppy's OneDrive path.
# ---------------------------------------------------------------------------
_BUNDLED_WORKBOOK = Path(__file__).resolve().parent / "SDR Parameters.xlsx"
_POPPY_WORKBOOK = Path(
    "/Users/poppy/Library/CloudStorage/OneDrive-SharedLibraries-JohnsHopkins/"
    "Meibin Chen - MOMISH interventions/SDR Parameters.xlsx"
)


def _default_workbook_path() -> Path:
    env = os.environ.get("SDR_PARAMS_PATH")
    if env:
        return Path(env)
    if _BUNDLED_WORKBOOK.exists():
        return _BUNDLED_WORKBOOK
    return _POPPY_WORKBOOK


WORKBOOK_PATH: Path = _default_workbook_path()'''
    start = text.index("# ---------------------------------------------------------------------------\n# Module-level workbook path")
    end = text.index("DEFAULT_COUNTY:", start)
    text = text[:start] + bundled + "\n" + text[end:]
    p.write_text(text)
    print("patched sim/parameter_loader.py workbook default")
PY

echo "Done. Re-run: cd sdr-api && PYTHONPATH=../sim pytest tests/test_api.py::test_run_status_quo_quick -m slow"
