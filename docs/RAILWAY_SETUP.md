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

## 1. Connect GitHub

1. Railway → your project → **Settings**
2. **Connect repo:** `Ayoyemit/sdr_dashboard`
3. **Deploy branch:** `feature/new-ui` (or merge to `main` and use `main`)

---

## 2. Service: sdr-api

| Setting | Value |
|---------|--------|
| **Root Directory** | *(empty — repository root)* |
| **Config file** | `railway.toml` at repo root |
| **Builder** | Dockerfile (`sdr-api/Dockerfile`) |

**Environment variables**

```env
ALLOWED_ORIGINS=https://<your-web-service-domain>,http://localhost:3000
```

Optional:

```env
RUN_CACHE_TTL_SECONDS=900
SDR_PARAMS_PATH=/app/sim/SDR Parameters.xlsx
```

**Health check:** `GET /health` → `{"status":"ok"}` (JSON, not plain `OK`).

Copy the **public URL** (e.g. `https://sdr-api-production-xxxx.up.railway.app`).

---

## 3. Service: sdr-web

| Setting | Value |
|---------|--------|
| **Root Directory** | `sdr-web` |
| **Config file** | `sdr-web/railway.toml` |
| **Builder** | Dockerfile (`Dockerfile` relative to `sdr-web/`) |

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
| Web: `working directory "/app" does not exist` | Set **Root Directory** to `sdr-web` and use Dockerfile builder (not Nixpacks with wrong root) |
| API build fails: `COPY sim/` | **Root Directory** must be repo root, not `sdr-api/` |
| Web loads but runs fail (CORS) | Set `ALLOWED_ORIGINS` to exact web URL |
| Web can’t reach API | Set `NEXT_PUBLIC_API_BASE` and **redeploy sdr-web** |
| Push doesn’t trigger deploy | Match Railway branch to `feature/new-ui` or push to `main` |
| Old Streamlit app deploys | Remove legacy Streamlit service; use Docker + Nixpacks (`Procfile.streamlit` is local-only) |

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
