# Deployment Guide — $0/mo (Render Free)

Deploy MemoryOS + MemoryOS-Showcase on Render Free tier.
512MB RAM, 750 hours/month, no credit card required.

---

## Architecture

```
GitHub: Abhii-07/MemoryOS               (engine library — no deploy)
GitHub: Abhii-07/MemoryOS-Application   (deployed product)
                 │
                 ▼
        ┌────────────────────┐
        │  Render Free       │  ← API (1 service, 750 hrs/mo)
        │  memoryos-api      │
        │  512MB RAM         │
        │                    │
        │  11 endpoints:     │
        │  /ingest           │  ← Showcase playground
        │  /ask              │  ← Showcase playground
        │  /memory           │  ← Showcase playground
        │  /audit            │  ← Showcase playground
        │  /assist*          │  ← Showcase (LLM)
        │  /chat             │  ← Showcase (LLM)
        │  /healthz          │  ← probe
        │  /v1/memory/turns  │  ← MemoryOS contract
        │  /v1/memory/query  │  ← MemoryOS contract
        │  DELETE /v1/memory/{id}   │  ← MemoryOS contract
        │  /v1/memory/deletion-status/{id} │
        └────────┬───────────┘
                 │
        ┌────────┴───────────┐
        │  Vercel (Free)     │  ← Next.js site
        │  site/ root dir    │
        └────────────────────┘
```

---

## Prerequisites

| Account | URL | Purpose | Card? |
|---------|-----|---------|-------|
| Render | render.com | Free API hosting | No |
| Neon | neon.tech | Free Postgres + pgvector | No |
| Vercel | vercel.com | Free Next.js hosting | No |
| OpenRouter | openrouter.ai | Free LLM API key | No |
| GitHub | github.com | Code (already done) | — |

---

## Part 1: Database (Neon)

### 1.1 Create project

1. Sign in to [neon.tech](https://neon.tech)
2. **Create Project** — name: `memoryos`, Postgres **17**
3. Copy connection string:
   ```
   postgresql://neondb_owner:xxxx@ep-xxx.us-east-2.aws.neon.tech/memoryos?sslmode=require
   ```

### 1.2 Enable pgvector

In Neon **SQL Editor**:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 1.3 Showcase database (optional — same DB works for both)

The merged API uses ONE database. Skip the second DB unless you want
tenant separation between the two surfaces. If you create it:

1. **Databases** → **Create Database** → `memoryos_showcase`
2. `CREATE EXTENSION IF NOT EXISTS vector;` on it

---

## Part 2: OpenRouter API Key

1. [openrouter.ai](https://openrouter.ai) → sign up → **Keys** → **Create Key**
2. Copy key (`sk-or-v1-...`)
3. Free model: `meta-llama/llama-3.3-70b-instruct:free`

---

## Part 3: Deploy API (Render Free)

### 3.1 Create service

1. Sign in to [render.com](https://render.com)
2. **New** → **Web Service**
3. Connect GitHub repo: `Abhii-07/MemoryOS-Application`
4. Settings:
   - **Name:** `memoryos-api`
   - **Region:** Oregon (us-west) or nearest
   - **Runtime:** Docker
   - **Dockerfile path:** `./server/Dockerfile`
   - **Docker context:** repo root
   - **Instance type:** **Free** ($0/mo)
   - **Health Check Path:** `/healthz`

### 3.2 Environment variables

| Key | Value |
|-----|-------|
| `MEMORYOS_DB_DSN` | `postgresql://neondb_owner:xxxx@ep-xxx/memoryos?sslmode=require` |
| `CORS_ORIGINS` | `https://your-app.vercel.app` (add after Part 4) |
| `MEMORYOS_ASSIST_PROVIDER` | `openrouter` |
| `OPENROUTER_API_KEY` | `sk-or-v1-...` |
| `OPENROUTER_MODEL` | `meta-llama/llama-3.3-70b-instruct:free` |

### 3.3 Deploy

1. Click **Create Web Service**
2. Build: ~5-8 min (torch CPU ~1.5GB image)
3. Verify:
   ```
   curl https://memoryos-api.onrender.com/healthz
   # → {"status":"ok"}
   ```

### 3.4 Test contract endpoints

```bash
# Admit a turn
curl -X POST https://memoryos-api.onrender.com/v1/memory/turns \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"test","user_id":"u1","text":"I prefer dark mode","turn_type":"user","timestamp":"2026-08-17T12:00:00Z"}'

# Query
curl -X POST https://memoryos-api.onrender.com/v1/memory/query \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"test","user_id":"u1","query_text":"what UI do I prefer?","token_budget":2048}'

# Delete (use record_id from above)
curl -X DELETE https://memoryos-api.onrender.com/v1/memory/{record_id} \
  -H "X-Tenant-ID: test" -H "X-User-ID: u1"
```

---

## Part 4: Deploy Site (Vercel)

### 4.1 Import

1. [vercel.com](https://vercel.com) → **Add New** → **Project**
2. Import `Abhii-07/MemoryOS-Application`
3. **Root Directory:** `site`
4. Framework: **Next.js** (auto)

### 4.2 Environment variables

| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_MEMORY_API_URL` | `https://memoryos-api.onrender.com` |
| `NEXT_PUBLIC_MEMORY_ENGINE` | `api` |

### 4.3 Deploy

1. Click **Deploy**
2. URL: `https://memoryos-application-xxxx.vercel.app`
3. **Back to Render** → `memoryos-api` → Environment → set
   `CORS_ORIGINS=https://memoryos-application-xxxx.vercel.app`
4. Manual Deploy → Deploy latest commit (or wait for auto-deploy)

---

## Part 5: Verification Checklist

| Check | URL | Expected |
|-------|-----|----------|
| Healthz | `https://memoryos-api.onrender.com/healthz` | `{"status":"ok"}` |
| Site | `https://your-app.vercel.app` | Landing loads |
| Playground | `/playground` | Ingest + ask work |
| Chat | `/playground` → Chat | LLM grounded reply |
| Contract turns | `POST /v1/memory/turns` | 200 + admission_op |
| Contract query | `POST /v1/memory/query` | memory_found or no_relevant_memory |
| Contract delete | `DELETE /v1/memory/{id}` | 200 complete / 202 in_progress |

---

## Part 6: Performance Monitoring

Render dashboard → `memoryos-api` → **Metrics** tab shows CPU + memory
live. Track these:

| Metric | Expected | Watch for |
|--------|----------|-----------|
| Memory RSS | 350-450MB peak (after 1st request) | >480MB = near OOM |
| Memory idle | ~120-150MB (before 1st request) | — |
| CPU | <10% idle, spikes on embed | Sustained >90% |
| Cold start | ~1 min (Render spin-up) + ~5-10s torch load | >2 min |
| Warm p95 | <200ms retrieval | >500ms |
| Spin-downs | After 15 min idle | Many/day is normal (free tier) |

**Keep-warm (optional):** free cron at [cron-job.org](https://cron-job.org)
pinging `https://memoryos-api.onrender.com/healthz` every 10 min.
Note: free tier still counts those hours against the 750/mo budget.

**Hour budget:** 750 hrs/mo = 25 hrs/day. Spun-down instances use 0 hrs.
If suspended, wait for month reset or upgrade to Starter ($7).

---

## Part 7: Troubleshooting

### OOM (service restarts, 503s)
- First request after spin-up loads torch (~250MB). One worker only.
- Check Render logs for `Killed` / `MemoryError`.
- Mitigations: `OMP_NUM_THREADS=2` (set in Dockerfile), avoid concurrent
  first-requests hitting the lazy init simultaneously.
- Upgrade path: Starter ($7) — just change instance type in dashboard.

### Slow cold start
- Normal for free tier: ~1 min spin-up + model load.
- cron-job.org keep-alive every 10 min reduces frequency.
- Upgrade path: Starter stays warm (no spin-down).

### Build fails / slow build
- torch CPU download is ~200MB. Free tier build can take 5-8 min.
- 500 build-minutes/month included; a failed build also counts.
- `docker system prune` equivalent: delete the service's build cache in
  Render dashboard → Builds tab.

### Chat returns "no assistant provider configured"
- `OPENROUTER_API_KEY` missing/empty on Render.
- Key invalid → regenerate at openrouter.ai/keys.

### Neon connection refused
- `sslmode=require` present?
- Neon free pauses after inactivity → **Resume** in dashboard.
- Check Neon not in "paused" state under Project → Settings → Compute.

### 503 from healthz
- Postgres unreachable → Neon paused or wrong DSN.
- Check `docker logs` equivalent: Render → Logs tab.

---

## Cost Summary

| Service | Tier | Monthly |
|---------|------|---------|
| Render (API) | Free | $0 |
| Neon (Postgres) | Free | $0 |
| Vercel (Site) | Free | $0 |
| OpenRouter (LLM) | Free tier | $0 |
| **Total** | | **$0** |

---

## Provider-Agnostic Upgrade Path

The compute layer can change without touching MemoryOS core:

| Move | What changes | Code changes |
|------|-------------|--------------|
| Free → Starter | Render dashboard: instance type | None |
| Render → Railway/Fly/VPS | New Dockerfile CMD, CORS origin | None (core untouched) |
| CPU → GPU torch | Dockerfile pip index URL | None (core untouched) |
| OpenRouter → OpenAI/Anthropic | `MEMORYOS_ASSIST_PROVIDER` env | None (core untouched) |
| Neon → Supabase/RDS | `MEMORYOS_DB_DSN` env | None (core untouched) |
