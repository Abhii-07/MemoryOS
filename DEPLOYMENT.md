# Deployment Guide — $0/mo

Deploy MemoryOS + MemoryOS-Showcase on Oracle Cloud Always Free tier.
4 ARM cores, 24GB RAM, free forever.

---

## Prerequisites

| Account | URL | Purpose |
|---------|-----|---------|
| Oracle Cloud | cloud.oracle.com | Free ARM VM |
| Neon | neon.tech | Free Postgres + pgvector |
| Vercel | vercel.com | Free Next.js hosting |
| OpenRouter | openrouter.ai | Free LLM API key |

---

## Part 1: Oracle Cloud VM

### 1.1 Create account

1. Go to [cloud.oracle.com](https://cloud.oracle.com)
2. Sign up for **Always Free** account (needs credit card for verification, not charged)
3. Verify email

### 1.2 Create ARM instance

1. Dashboard → **Create a VM instance**
2. Settings:
   - **Name:** `memoryos`
   - **Image:** Ubuntu 22.04 or 24.04 (aarch64/ARM)
   - **Shape:** **VM.Standard.A1.Flex** (Always Free eligible)
     - OCPUs: **4** (max free)
     - Memory: **24 GB** (max free)
   - **Boot volume:** 50 GB (free tier allows up to 200GB)
3. **Add SSH keys:** Upload your public key or generate new one
4. **Networking:** Create a new VCN with internet access (default is fine)
5. Click **Create**
6. **Note the public IP** (e.g., `129.1xx.xxx.xxx`)

### 1.3 Open ports

1. Go to **Networking** → **Virtual Cloud Networks** → your VCN
2. **Security Lists** → **Default Security List** → **Add Ingress Rules**
3. Add:
   | Protocol | Port | Source |
   |----------|------|--------|
   | TCP | 80 | 0.0.0.0/0 |
   | TCP | 443 | 0.0.0.0/0 |
   | TCP | 22 | Your IP only |

### 1.4 Connect

```bash
ssh -i ~/.ssh/your_key.pem ubuntu@129.1xx.xxx.xxx
```

---

## Part 2: Database (Neon)

### 2.1 Create Neon project

1. Sign in to [neon.tech](https://neon.tech)
2. **Create Project**:
   - Name: `memoryos`
   - Postgres version: **17**
3. **Copy connection string:**
   ```
   postgresql://neondb_owner:xxxx@ep-xxx.us-east-2.aws.neon.tech/memoryos?sslmode=require
   ```

### 2.2 Enable pgvector

In Neon **SQL Editor**:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2.3 Create Showcase database

1. **Databases** → **Create Database** → name: `memoryos_showcase`
2. Enable pgvector:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

You now have two connection strings:
- **MemoryOS:** `postgresql://neondb_owner:xxxx@ep-xxx/memoryos?sslmode=require`
- **Showcase:** `postgresql://neondb_owner:xxxx@ep-xxx/memoryos_showcase?sslmode=require`

---

## Part 3: OpenRouter API Key

1. Go to [openrouter.ai](https://openrouter.ai)
2. Sign up → **Keys** → **Create Key**
3. Copy key (`sk-or-v1-...`)
4. Free tier: `meta-llama/llama-3.3-70b-instruct:free`

---

## Part 4: Deploy (one command)

### 4.1 SSH into your VM

```bash
ssh -i ~/.ssh/your_key.pem ubuntu@129.1xx.xxx.xxx
```

### 4.2 Run the setup script

Set your env vars and run:

```bash
export MEMORYOS_DB_DSN="postgresql://neondb_owner:xxxx@ep-xxx/memoryos?sslmode=require"
export MEMORYOS_DB_DSN_SHOWCASE="postgresql://neondb_owner:xxxx@ep-xxx/memoryos_showcase?sslmode=require"
export OPENROUTER_API_KEY="sk-or-v1-xxxx"

curl -sL https://raw.githubusercontent.com/Abhii-07/MemoryOS/main/deploy/setup.sh | bash
```

Or clone and run manually:

```bash
git clone https://github.com/Abhii-07/MemoryOS.git /opt/memoryos/repos/MemoryOS
git clone https://github.com/Abhii-07/MemoryOS-Application.git /opt/memoryos/repos/MemoryOS-Showcase

cd /opt/memoryos
# set env vars above, then:
bash deploy/setup.sh
```

### 4.3 What the script does

1. Installs Docker + Docker Compose
2. Clones both repos
3. Builds Docker images (~5-10 min first time)
4. Starts 3 containers: `memoryos-api`, `showcase-api`, `nginx`
5. Prints your public URL

### 4.4 Verify

```bash
# Health checks
curl http://YOUR_IP/healthz/memoryos
curl http://YOUR_IP/healthz/showcase

# Test MemoryOS API
curl -X POST http://YOUR_IP/api/memory/turns \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"test","user_id":"user1","text":"I prefer dark mode","turn_type":"user","timestamp":"2026-08-17T12:00:00Z"}'
```

---

## Part 5: Showcase Frontend (Vercel)

### 5.1 Import project

1. Sign in to [vercel.com](https://vercel.com)
2. **Add New** → **Project**
3. Import `Abhii-07/MemoryOS-Application`
4. **Root Directory:** `site`
5. Framework: **Next.js** (auto-detected)

### 5.2 Environment Variables

| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_MEMORY_API_URL` | `http://YOUR_VM_IP/showcase` |
| `NEXT_PUBLIC_MEMORY_ENGINE` | `api` |

### 5.3 Deploy

1. Click **Deploy**
2. Vercel gives you: `https://memoryos-application-xxxx.vercel.app`

### 5.4 Update CORS

On your VM, edit `/opt/memoryos/docker-compose.prod.yml`:
```yaml
CORS_ORIGINS: "https://memoryos-application-xxxx.vercel.app"
```

Restart:
```bash
cd /opt/memoryos
docker compose -f docker-compose.prod.yml up -d --force-recreate showcase-api
```

---

## Part 6: SSL (optional but recommended)

### 6.1 Point domain to VM

1. Buy a domain or use a free subdomain (e.g., [sslip.io](https://sslip.io))
2. Create DNS A record → your VM IP

### 6.2 Get free SSL cert

```bash
sudo apt install -y certbot
sudo certbot certonly --standalone -d yourdomain.com
```

### 6.3 Update nginx config

Edit `/opt/memoryos/nginx.conf`:
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    # ... rest same
}
```

Copy certs:
```bash
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/memoryos/certs/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/memoryos/certs/
sudo docker compose -f /opt/memoryos/docker-compose.prod.yml restart nginx
```

---

## Cost Summary

| Service | Tier | Monthly |
|---------|------|---------|
| Oracle Cloud (VM) | Always Free | $0 |
| Neon (Postgres) | Free | $0 |
| Vercel (Site) | Free | $0 |
| OpenRouter (LLM) | Free tier | $0 |
| **Total** | | **$0** |

---

## Troubleshooting

### Build fails — OOM
Oracle Cloud ARM has 24GB RAM. Shouldn't happen. If it does:
```bash
docker system prune -a
cd /opt/memoryos && docker compose -f docker-compose.prod.yml build --no-cache
```

### Neon connection refused
- Check `sslmode=require` in DSN
- Neon free tier pauses after inactivity → click **Resume** in dashboard

### Vercel site shows "Application error"
- Check `NEXT_PUBLIC_MEMORY_API_URL` points to your VM IP
- Check VM security list allows inbound on port 80
- Check CORS includes Vercel domain

### Cold start slow (~30s)
Normal. torch + sentence-transformers load on first request. Subsequent requests are fast.
To keep warm, add a cron:
```bash
*/5 * * * * curl -s http://localhost:8000/healthz > /dev/null
```

### Service won't start
```bash
cd /opt/memoryos
docker compose -f docker-compose.prod.yml logs memoryos-api
docker compose -f docker-compose.prod.yml logs showcase-api
```

### Update code after git push
```bash
cd /opt/memoryos/repos/MemoryOS && git pull
cd /opt/memoryos/repos/MemoryOS-Showcase && git pull
cd /opt/memoryos
docker compose -f docker-compose.prod.yml up -d --build
```
