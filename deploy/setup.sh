#!/usr/bin/env bash
# ── Oracle Cloud Always Free — MemoryOS deployment ──────────────────────────
# Run as root on a fresh Ubuntu 22.04/24.04 ARM instance.
# Usage: curl -sL https://raw.githubusercontent.com/Abhii-07/MemoryOS/main/deploy/setup.sh | bash
#
# What this does:
#   1. Installs Docker + Docker Compose
#   2. Clones both repos (MemoryOS + MemoryOS-Showcase)
#   3. Builds and starts: MemoryOS API + Showcase API + Nginx
#   4. Outputs the public URL and next steps
#
# Required env vars (pass before running):
#   MEMORYOS_DB_DSN     — Neon Postgres connection string
#   OPENROUTER_API_KEY  — OpenRouter API key

set -euo pipefail

# ── colors ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[+]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[x]${NC} $*"; exit 1; }

# ── preflight ────────────────────────────────────────────────────────────────
[[ $EUID -eq 0 ]] || error "Run as root: sudo bash setup.sh"
[[ -n "${MEMORYOS_DB_DSN:-}" ]]  || error "Set MEMORYOS_DB_DSN env var"
[[ -n "${OPENROUTER_API_KEY:-}" ]] || error "Set OPENROUTER_API_KEY env var"

DEPLOY_DIR="/opt/memoryos"
REPOS_DIR="${DEPLOY_DIR}/repos"

# ── 1. system deps ───────────────────────────────────────────────────────────
info "Installing Docker..."
if ! command -v docker &>/dev/null; then
    apt-get update -qq
    apt-get install -y -qq ca-certificates curl gnupg lsb-release
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
fi
info "Docker: $(docker --version)"

# ── 2. clone repos ───────────────────────────────────────────────────────────
mkdir -p "$REPOS_DIR"
cd "$REPOS_DIR"

if [ ! -d "MemoryOS" ]; then
    info "Cloning MemoryOS..."
    git clone https://github.com/Abhii-07/MemoryOS.git
fi
if [ ! -d "MemoryOS-Showcase" ]; then
    info "Cloning MemoryOS-Showcase..."
    git clone https://github.com/Abhii-07/MemoryOS-Application.git MemoryOS-Showcase
fi

# ── 3. create production docker-compose ──────────────────────────────────────
info "Writing docker-compose.prod.yml..."
cat > "${DEPLOY_DIR}/docker-compose.prod.yml" <<'YAML'
services:
  memoryos-api:
    build:
      context: /opt/memoryos/repos/MemoryOS
      dockerfile: Dockerfile
    container_name: memoryos-api
    restart: unless-stopped
    environment:
      MEMORYOS_DB_DSN: "${MEMORYOS_DB_DSN}"
      CORS_ORIGINS: "*"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"]
      interval: 30s
      timeout: 5s
      retries: 3

  showcase-api:
    build:
      context: /opt/memoryos/repos/MemoryOS-Showcase
      dockerfile: server/Dockerfile
    container_name: showcase-api
    restart: unless-stopped
    environment:
      MEMORYOS_DB_DSN: "${MEMORYOS_DB_DSN_SHOWCASE}"
      CORS_ORIGINS: "https://${DOMAIN:-localhost}"
      MEMORYOS_ASSIST_PROVIDER: "openrouter"
      OPENROUTER_API_KEY: "${OPENROUTER_API_KEY}"
      OPENROUTER_MODEL: "meta-llama/llama-3.3-70b-instruct:free"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"]
      interval: 30s
      timeout: 5s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /opt/memoryos/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - /opt/memoryos/certs:/etc/nginx/certs:ro
    depends_on:
      - memoryos-api
      - showcase-api
YAML

# ── 4. nginx config ──────────────────────────────────────────────────────────
info "Writing nginx.conf..."
cat > "${DEPLOY_DIR}/nginx.conf" <<'NGINX'
upstream memoryos_api {
    server memoryos-api:8000;
}
upstream showcase_api {
    server showcase-api:8000;
}

server {
    listen 80;
    server_name _;

    # MemoryOS API
    location /api/ {
        proxy_pass http://memoryos_api/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Showcase API
    location /showcase/ {
        proxy_pass http://showcase_api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health checks
    location /healthz/memoryos {
        proxy_pass http://memoryos_api/healthz;
    }
    location /healthz/showcase {
        proxy_pass http://showcase_api/healthz;
    }

    # Default — show status
    location / {
        return 200 '{"services":{"memoryos":"/api/","showcase":"/showcase/","healthz":"/healthz/memoryos"}}';
        add_header Content-Type application/json;
    }
}
NGINX

# ── 5. build and start ───────────────────────────────────────────────────────
info "Building Docker images (this takes ~5-10 min)..."
cd "$DEPLOY_DIR"
docker compose -f docker-compose.prod.yml build

info "Starting services..."
docker compose -f docker-compose.prod.yml up -d

# ── 6. wait for health ──────────────────────────────────────────────────────
info "Waiting for services to become healthy..."
sleep 10
for svc in memoryos-api showcase-api; do
    for i in $(seq 1 30); do
        if docker inspect --format='{{.State.Health.Status}}' "$svc" 2>/dev/null | grep -q healthy; then
            info "$svc: healthy"
            break
        fi
        sleep 5
    done
done

# ── 7. summary ───────────────────────────────────────────────────────────────
PUBLIC_IP=$(curl -s http://ifconfig.me || echo "YOUR_IP")
echo ""
echo "════════════════════════════════════════════════════════════════"
info "Deployment complete!"
echo ""
echo "  MemoryOS API:   http://${PUBLIC_IP}/api/"
echo "  Showcase API:   http://${PUBLIC_IP}/showcase/"
echo "  Healthz:        http://${PUBLIC_IP}/healthz/memoryos"
echo "                  http://${PUBLIC_IP}/healthz/showcase"
echo ""
echo "  Next steps:"
echo "    1. Point your domain DNS to ${PUBLIC_IP}"
echo "    2. Set up SSL with: certbot --nginx -d yourdomain.com"
echo "    3. Update Vercel env: NEXT_PUBLIC_MEMORY_API_URL=https://yourdomain.com/showcase"
echo "    4. Update CORS_ORIGINS on both services to include your Vercel URL"
echo "════════════════════════════════════════════════════════════════"
