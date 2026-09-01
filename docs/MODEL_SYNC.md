# Model sync and deployment

This document explains how the Python simulation model is sourced, synced from Poppy’s deploy repo, and how changes reach Railway.

## Architecture

```
sdr-web (Next.js)  →  sdr-api (FastAPI)  →  sim/ (Python ABM + workbook)
                                              ↑
                         synced from Poppy’s sdr-dashboard-deploy
```

- **sdr-web** talks only to **sdr-api** (REST). It does not connect to Streamlit or Poppy’s deploy frontend.
- **sdr-api** imports Python modules from **`sim/`** (`PYTHONPATH` / Docker copy).
- **`scenario_to_sim.py`** + **`runner.py`** are your adapter layer (equivalent to scenario config in the Streamlit app).

## Source of truth (by layer)

| Layer | Upstream source of truth | What actually runs in production |
|-------|--------------------------|----------------------------------|
| Simulation Python | [sdr-dashboard-deploy](https://github.com/Poppyandnucky/sdr-dashboard-deploy) | Committed files in **`sim/`** in this repo |
| Parameters workbook | Poppy’s **SDR Parameters - Intervention** (OneDrive); also in deploy as `data/SDR Parameters.xlsx` | **`sim/SDR Parameters.xlsx`** (bundled in repo / Docker image) |
| Web UI + API | This repo (`sdr-web`, `sdr-api`) | Whatever is deployed from **your git branch** on Railway |
| Legacy Streamlit UI | `sim/SDR_Dash.py` | Reference only — not the production path |

**Important:** Poppy’s deploy repo is the **upstream model** source. Your **committed `sim/` folder** is what Railway runs until you sync again and redeploy.

## Connect to Poppy’s deploy repo

The git remote is named **`deploy`** (read-only usage):

```bash
# One-time setup (already done if `git remote -v` shows deploy)
git remote add deploy https://github.com/Poppyandnucky/sdr-dashboard-deploy.git
```

Verify:

```bash
git remote -v
# deploy  https://github.com/Poppyandnucky/sdr-dashboard-deploy.git (fetch)
```

## Sync model files into `sim/`

Use the project script (recommended):

```bash
./scripts/sync-sim-from-deploy.sh
```

This will:

1. `git fetch deploy main`
2. Copy core `.py` files from deploy repo root → `sim/`
3. Copy `data/SDR Parameters.xlsx` → `sim/SDR Parameters.xlsx`
4. Restore **`sim/SDR Parameters.xlsx`** as the default workbook path in `parameter_loader.py` (deploy’s copy may point at Poppy’s OneDrive)

If Poppy sends a **newer Excel only on OneDrive**, replace the workbook manually **before or after** sync:

```bash
cp /path/to/downloaded/SDR\ Parameters.xlsx "sim/SDR Parameters.xlsx"
```

### After every sync

```bash
cd sdr-api
PYTHONPATH=../sim pytest tests/ -q
```

Optional smoke script (local pytest + HTTP checks if API is running):

```bash
./scripts/smoke-test-deploy.sh
API_BASE=https://your-api.up.railway.app ./scripts/smoke-test-deploy.sh
```

## Workbook path (local vs Railway)

`sim/parameter_loader.py` resolves the workbook in this order:

1. Environment variable **`SDR_PARAMS_PATH`** (if set)
2. Bundled **`sim/SDR Parameters.xlsx`** (default for this repo)
3. Poppy’s OneDrive path (fallback for her machine only)

On Railway, the API Dockerfile copies `sim/` into the image; you usually **do not** need `SDR_PARAMS_PATH`. Optional override:

```bash
SDR_PARAMS_PATH=/app/sim/SDR Parameters.xlsx
```

## Commit and push so Railway updates

Railway deploys from **your connected GitHub repo** when you push to the branch each service tracks (typically `feature/new-ui` or `main`).

### 1. Review what will ship

```bash
git status
git diff --stat
```

Do **not** commit temp folders (e.g. `.tmp-ppt-images/`).

### 2. Run checks locally

```bash
# API tests
cd sdr-api && PYTHONPATH=../sim pytest tests/ -q

# Web build
cd ../sdr-web && npm run build
```

### 3. Stage, commit, push

```bash
cd /path/to/SDR-Dashboard-2026

git add sim/ sdr-api/ sdr-web/ scripts/ docs/
# Add any other intentional paths; avoid git add . unless you have reviewed untracked files

git commit -m "Describe what changed and why"

git push ayoyemit feature/new-ui
```

Use your remote name and branch as configured (`git branch -vv` shows tracking).

### 4. Railway redeploy

If Railway is linked to **ayoyemit/sdr_dashboard** (or this repo) and watches **`feature/new-ui`**:

- Pushing triggers **automatic** rebuilds for **sdr-api** and **sdr-web** (two separate services).
- In the Railway dashboard, confirm both services show a new deployment for your commit SHA.

If auto-deploy is off: Railway → each service → **Deploy** → **Redeploy** latest commit.

### 5. Environment variables (verify once)

**sdr-api**

| Variable | Example |
|----------|---------|
| `ALLOWED_ORIGINS` | `https://your-web.up.railway.app,http://localhost:3000` |
| `SDR_PARAMS_PATH` | Optional; see above |

**sdr-web**

| Variable | Example |
|----------|---------|
| `NEXT_PUBLIC_API_BASE` | `https://your-api.up.railway.app` |

`NEXT_PUBLIC_*` is baked in at **build time**. If you change the API URL, **redeploy sdr-web** after updating the variable.

### 6. Smoke test production

```bash
API_BASE=https://your-api.up.railway.app ./scripts/smoke-test-deploy.sh
```

Manual checks in the browser:

- County switch (Kakamega, Kisii, Makueni, Mombasa) → run reflects selected county
- FQA/PULSE on Design → no “not wired” warnings; results differ from off
- Results show assumptions banner and county scope

## Typical workflow when Poppy updates the model

1. `./scripts/sync-sim-from-deploy.sh`
2. Apply newer OneDrive workbook if she sent one outside deploy
3. `cd sdr-api && PYTHONPATH=../sim pytest tests/ -q`
4. `git add sim/` (+ any API adapter fixes if needed)
5. `git commit` → `git push ayoyemit feature/new-ui`
6. Wait for Railway **sdr-api** deploy; run smoke tests
7. Redeploy **sdr-web** only if you changed frontend or `NEXT_PUBLIC_API_BASE`

## What we do **not** sync from deploy

Do not copy into production paths:

- `frontend/` (HTML/Streamlit companion)
- `SDR_Dash_TI.py` and Streamlit-only launchers

Those are reference for parity with the old UI only.

## Related files

| Path | Purpose |
|------|---------|
| `scripts/sync-sim-from-deploy.sh` | Pull model + workbook from `deploy/main` |
| `scripts/smoke-test-deploy.sh` | Post-deploy API smoke tests |
| `sdr-api/Dockerfile` | Copies `sim/` into API image |
| `sdr-api/app/adapters/scenario_to_sim.py` | Maps API scenarios → sim flags |
| `sdr-api/railway.toml` | API Railway build (Dockerfile) |
| `sdr-web/railway.toml` | Web Railway build (Nixpacks) |
