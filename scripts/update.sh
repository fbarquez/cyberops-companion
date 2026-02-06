#!/bin/bash
# =============================================================================
# CyberOps Companion - Update Script (Zero-Downtime)
# =============================================================================
# Run this to update the application after pushing new code
# =============================================================================
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗"
echo "║           CyberOps Companion - Update                         ║"
echo "╚═══════════════════════════════════════════════════════════════╝${NC}"

# Check if running in correct directory
if [ ! -f docker-compose.prod.yml ]; then
    echo -e "${RED}Error: docker-compose.prod.yml not found${NC}"
    echo "Run this script from the project root directory"
    exit 1
fi

# Pull latest code
if [ -d .git ]; then
    echo -e "${BLUE}Pulling latest changes...${NC}"
    git pull origin main
    echo -e "${GREEN}✓ Code updated${NC}"
fi

# Build new images
echo -e "${BLUE}Building new images...${NC}"
docker compose -f docker-compose.prod.yml build

# Rolling update - one service at a time
echo -e "${BLUE}Updating API service...${NC}"
docker compose -f docker-compose.prod.yml up -d --no-deps api
sleep 5

echo -e "${BLUE}Updating Web service...${NC}"
docker compose -f docker-compose.prod.yml up -d --no-deps web
sleep 5

echo -e "${BLUE}Updating Celery workers...${NC}"
docker compose -f docker-compose.prod.yml up -d --no-deps celery-worker celery-beat

# Run migrations
echo -e "${BLUE}Running database migrations...${NC}"
docker compose -f docker-compose.prod.yml exec -T api alembic upgrade head || true

# Restart Caddy to pick up any changes
echo -e "${BLUE}Restarting Caddy...${NC}"
docker compose -f docker-compose.prod.yml restart caddy

# Cleanup old images
echo -e "${BLUE}Cleaning up old images...${NC}"
docker image prune -f

echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    Update Complete!                            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Show status
docker compose -f docker-compose.prod.yml ps
