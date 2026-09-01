# Railway setup (two-service monorepo)

Use this when connecting **Ayoyemit/sdr_dashboard** to Railway. I do not have access to your Railway account from the dev environment — you must apply these settings in the [Railway dashboard](https://railway.app).

## Why auto-deploy may have stopped

| Before | Now |
|--------|-----|
| One service on `main` running Streamlit (`Procfile`) | Two services: **sdr-api** + **sdr-web** |
| Pushes to `main` | Recent work is on **`feature/new-ui`** |
| Single process | API Dockerfile needs **repo root** build context (`sim/` + `sdr-api/`) |

Pushing to `ayoyemit feature/new-ui` does **not** redeploy if Railway still watches **`main`** or only has a Streamlit service.

---

## Your Railway project (Ayoyemi2)

| Railway service | Role | URL | Root directory |
|-----------------|------|-----|----------------|
| **`web`** | FastAPI API | `https://web-production-41670.up.railway.app` | *(repo root)* |
| **`sdr_dashboard`** | Next.js UI | `https://sdr-kenya.up.railway.app` | `sdr-web` |

Env vars:

- **`web`:** `ALLOWED_ORIGINS` must include `https://sdr-kenya.up.railway.app`
- **`sdr_dashboard`:** `NEXT_PUBLIC_API_BASE=https://web-production-41670.up.railway.app`

Service names are easy to confuse — **`web` is the API**, **`sdr_dashboard` is the frontend**.

---

## 1. Connect GitHub

1. Railway → your project → **Settings**
2. **Connect repo:** `Ayoyemit/sdr_dashboard`
3. **Deploy branch:** `feature/new-ui` (or merge to `main` and use `main`)

---

## 2. Service: `web` (API)

| Setting | Value |
|---------|--------|
| **Root Directory** | *(empty — repository root)* |
| **Builder** | Dockerfile → `sdr-api/Dockerfile` |
| **Config file** | `sdr-api/railway.toml` |

**Environment variables**

```env
ALLOWED_ORIGINS=https://sdr-kenya.up.railway.app,http://localhost:3000
DISABLE_PREWARM=true
```

Optional:

```env
RUN_CACHE_TTL_SECONDS=900
```

**Health check:** `GET /health` → `{"status":"ok"}` (JSON, not plain `OK`).

**Deploy tab:** clear any custom **Start Command** or **Working Directory** override (leave empty).

---

## Docker vs Nixpacks

| Railway service | Builder | Why |
|-----------------|---------|-----|
| **`web`** | **Dockerfile** | Must copy `sim/` + `sdr-api/` from monorepo root |
| **`sdr_dashboard`** | **Nixpacks** | Standard Next.js in `sdr-web/` |

Do **not** put `railway.toml` at the **repo root** — Railway applies it to every service. Use `sdr-api/railway.toml` for **`web`** and `sdr-web/railway.toml` for **`sdr_dashboard`**.

`sdr-web/Dockerfile` is for **local** `docker compose` only.

---

## 3. Service: `sdr_dashboard` (frontend)

| Setting | Value |
|---------|--------|
| **Root Directory** | `sdr-web` ← **critical** |
| **Builder** | Railpack / Nixpacks (auto-detects Next.js) |
| **Dockerfile** | *(none — do not use API Dockerfile)* |
| **Config file** | *(none)* |

> If Root Directory is empty, or this service inherits `sdr-api/railway.toml`, the build fails (`/sim` or `/sdr-api` not found).

**Environment variables** (required at **build** time):

```env
NEXT_PUBLIC_API_BASE=https://<your-api-service-domain>
```

No trailing slash. Redeploy **sdr-web** after changing this variable.

---

## 4. Custom domains (optional)

Names like `sdr-api.railway.app` / `sdr-tool.railway.app` only work if you **attach** them to the correct service in Railway → **Settings → Networking**. Until then, use the generated `*.up.railway.app` URLs.

---

## 5. Verify deploy

```bash
# Replace with your real API URL from Railway
API_BASE=https://<api-domain> ./scripts/smoke-test-deploy.sh
```

Manual checks:

```bash
curl -s https://<api-domain>/health
# {"status":"ok"}

curl -s https://<api-domain>/api/v1/meta/counties
# {"counties":[{"id":"kakamega",...},...]}
```

Open the web URL → Design → Quick run → Results.

---

## 6. CLI (optional)

```bash
npx @railway/cli login
npx @railway/cli link      # pick project + service
npx @railway/cli up        # manual deploy
npx @railway/cli logs
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `/health` returns plain `OK` | Wrong service or placeholder — not your FastAPI app |
| Web: `working directory "/app" does not exist` | **Root Directory** must be `sdr-web` (not repo root). Clear any custom “Working Directory” override in Railway settings. |
| API build fails: `COPY sim/` | **Root Directory** must be repo root, not `sdr-api/` |
| Web loads but runs fail (CORS) | Set `ALLOWED_ORIGINS` to exact web URL |
| Web can’t reach API | Set `NEXT_PUBLIC_API_BASE` and **redeploy sdr-web** |
| Push doesn’t trigger deploy | Match Railway branch to `feature/new-ui` |
| Old Streamlit app deploys | Legacy `Procfile.streamlit` is local-only; not used by Railway |

---

## Push workflow

```bash
git add .
git commit -m "Your message"
git push ayoyemit feature/new-ui
```

If Railway watches `main`:

```bash
git push ayoyemit feature/new-ui:main
```

(Only if you intend to replace `main` with the new stack.)
