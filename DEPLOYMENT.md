# Deployment Guide

Step-by-step deployment for MemoryOS and MemoryOS-Showcase.

---

## Prerequisites

| Account | URL | Purpose |
|---------|-----|---------|
| GitHub | github.com | Code hosting (already done) |
| Neon | neon.tech | PostgreSQL + pgvector database |
| Render | render.com | API server hosting |
| Vercel | vercel.com | Next.js frontend hosting |
| OpenRouter | openrouter.ai | Free LLM API key |

---

## Part 1: Database (Neon)

### 1.1 Create Neon project

1. Sign in to [neon.tech](https://neon.tech)
2. Click **Create Project**
3. Settings:
   - Project name: `memoryos`
   - Postgres version: **17**
   - Region: **AWS US East (N. Virginia)** or closest to your users
4. Click **Create Project**
5. **Copy the connection string** — it looks like:
   ```
   postgresql://neondb_owner:xxxx@ep-xxx.us-east-2.aws.neon.tech/memoryos?sslmode=require
   ```

### 1.2 Enable pgvector extension

1. In Neon dashboard, go to **SQL Editor**
2. Run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Verify:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```

### 1.3 Create a second database for Showcase (if using same Neon project)

In the Neon dashboard:
1. Go to **Databases** → **Create Database**
2. Name: `memoryos_showcase`
3. Enable pgvector on it too:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

You now have two connection strings:
- MemoryOS: `postgresql://neondb_owner:xxxx@ep-xxx/memoryos?sslmode=require`
- Showcase: `postgresql://neondb_owner:xxxx@ep-xxx/memoryos_showcase?sslmode=require`

---

## Part 2: MemoryOS API (Render)

### 2.1 Create Web Service

1. Sign in to [render.com](https://render.com)
2. Click **New** → **Web Service**
3. Connect GitHub repo: `Abhii-07/MemoryOS`
4. Settings:
   - **Name:** `memoryos-api`
   - **Runtime:** Docker
   - **Dockerfile path:** `./Dockerfile`
   - **Docker context:** `.` (root)
   - **Instance type:** Starter ($7/mo) — 512MB RAM minimum
   - **Health Check Path:** `/healthz`

### 2.2 Environment Variables

Add these in the **Environment** tab:

| Key | Value |
|-----|-------|
| `MEMORYOS_DB_DSN` | `postgresql://neondb_owner:xxxx@ep-xxx/memoryos?sslmode=require` |
| `CORS_ORIGINS` | `*` (tighten later) |

### 2.3 Deploy

1. Click **Create Web Service**
2. First build takes ~5-8 min (torch + model download)
3. Once live, verify:
   ```
   curl https://memoryos-api.onrender.com/healthz
   ```
   Should return: `{"status":"ok"}`

### 2.4 Test endpoints

```bash
# Health check
curl https://memoryos-api.onrender.com/healthz

# Admit a turn
curl -X POST https://memoryos-api.onrender.com/v1/memory/turns \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "test",
    "user_id": "user1",
    "text": "I prefer dark mode in all my apps",
    "turn_type": "user",
    "timestamp": "2026-08-17T12:00:00Z"
  }'

# Query
curl -X POST https://memoryos-api.onrender.com/v1/memory/query \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "test",
    "user_id": "user1",
    "query_text": "what UI preference do I have?",
    "token_budget": 2048
  }'
```

---

## Part 3: Showcase API (Render)

### 3.1 Create Web Service

1. In Render dashboard, click **New** → **Web Service**
2. Connect GitHub repo: `Abhii-07/MemoryOS-Application`
3. Settings:
   - **Name:** `memoryos-showcase-api`
   - **Runtime:** Docker
   - **Dockerfile path:** `./server/Dockerfile`
   - **Docker context:** `.` (root)
   - **Instance type:** Starter ($7/mo)
   - **Health Check Path:** `/healthz`

### 3.2 Environment Variables

| Key | Value |
|-----|-------|
| `MEMORYOS_DB_DSN` | `postgresql://neondb_owner:xxxx@ep-xxx/memoryos_showcase?sslmode=require` |
| `CORS_ORIGINS` | `https://your-app.vercel.app,http://localhost:3000` |
| `MEMORYOS_ASSIST_PROVIDER` | `openrouter` |
| `OPENROUTER_API_KEY` | `sk-or-v1-xxxx` (from openrouter.ai) |
| `OPENROUTER_MODEL` | `meta-llama/llama-3.3-70b-instruct:free` |

### 3.3 Deploy

1. Click **Create Web Service**
2. Wait for build (~5-8 min)
3. Verify:
   ```
   curl https://memoryos-showcase-api.onrender.com/healthz
   ```

---

## Part 4: Showcase Frontend (Vercel)

### 4.1 Import project

1. Sign in to [vercel.com](https://vercel.com)
2. Click **Add New** → **Project**
3. Import GitHub repo: `Abhii-07/MemoryOS-Application`
4. **Important:** Set the **Root Directory** to `site`
5. Framework: **Next.js** (auto-detected)

### 4.2 Environment Variables

| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_MEMORY_API_URL` | `https://memoryos-showcase-api.onrender.com` |
| `NEXT_PUBLIC_MEMORY_ENGINE` | `api` |

### 4.3 Deploy

1. Click **Deploy**
2. Build takes ~1-2 min
3. Once live, Vercel gives you a URL like:
   ```
   https://memoryos-application-xxxx.vercel.app
   ```

### 4.4 Update CORS on Render

Go back to Render → `memoryos-showcase-api` → Environment:
1. Update `CORS_ORIGINS` to include your Vercel URL:
   ```
   https://memoryos-application-xxxx.vercel.app,http://localhost:3000
   ```
2. Service auto-redeploys

---

## Part 5: OpenRouter API Key

1. Go to [openrouter.ai](https://openrouter.ai)
2. Sign up / sign in
3. Go to **Keys** → **Create Key**
4. Copy the key (starts with `sk-or-v1-...`)
5. Paste into Render env var `OPENROUTER_API_KEY` for Showcase API
6. Free tier gives you access to `meta-llama/llama-3.3-70b-instruct:free`

---

## Verification Checklist

| Step | URL | Expected |
|------|-----|----------|
| MemoryOS healthz | `https://memoryos-api.onrender.com/healthz` | `{"status":"ok"}` |
| MemoryOS admit | `POST /v1/memory/turns` | 200 + admission_op |
| MemoryOS query | `POST /v1/memory/query` | 200 + memories or no_relevant_memory |
| Showcase API healthz | `https://memoryos-showcase-api.onrender.com/healthz` | `{"status":"ok"}` |
| Showcase site | `https://your-app.vercel.app` | Landing page loads |
| Showcase playground | `https://your-app.vercel.app/playground` | Can ingest + ask |
| Showcase chat | `https://your-app.vercel.app/playground` → Chat | LLM responds with memory context |

---

## Cost Summary

| Service | Tier | Monthly |
|---------|------|---------|
| Neon (Postgres) | Free | $0 |
| Render (MemoryOS API) | Starter | $7 |
| Render (Showcase API) | Starter | $7 |
| Vercel (Showcase Site) | Free | $0 |
| OpenRouter (LLM) | Free tier | $0 |
| **Total** | | **$14/mo** |

---

## Troubleshooting

### Render build fails with "out of memory"
- Torch download is large. Render free/starter may OOM during build.
- Solution: Upgrade to Render **Standard** ($20/mo) or pre-build Docker image locally and push to Docker Hub.

### Neon connection refused
- Check `sslmode=require` is in the DSN
- Check Neon project isn't paused (free tier pauses after inactivity)
- Click **Resume** in Neon dashboard

### Vercel site shows "Application error"
- Check `NEXT_PUBLIC_MEMORY_API_URL` is set correctly
- Check Render API is live (healthz returns ok)
- Check CORS includes your Vercel domain

### Chat returns "no assistant provider configured"
- Check `OPENROUTER_API_KEY` is set in Render env
- Check key is valid at openrouter.ai/keys

### Cold start takes 30+ seconds
- Normal for first request (embedder model loads ~3s, torch init)
- Subsequent requests are fast
- Render may spin down after inactivity on free tier
