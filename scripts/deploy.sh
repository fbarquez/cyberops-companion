#!/bin/bash
# =============================================================================
# CyberOps Companion - Production Deployment Script
# =============================================================================
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           CyberOps Companion - Production Deploy              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "${YELLOW}Copy .env.production.example to .env and configure it:${NC}"
    echo "  cp .env.production.example .env"
    echo "  nano .env"
    exit 1
fi

# Load environment variables
source .env

# Validate required variables
required_vars=("DOMAIN" "DB_USER" "DB_PASSWORD" "JWT_SECRET" "SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}Error: $var is not set in .env${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✓ Environment validated${NC}"

# Create necessary directories
echo -e "${BLUE}Creating directories...${NC}"
mkdir -p backups exports data

# Pull latest code (if using git)
if [ -d .git ]; then
    echo -e "${BLUE}Pulling latest changes from git...${NC}"
    git pull origin main
fi

# Build and deploy
echo -e "${BLUE}Building containers...${NC}"
docker compose -f docker-compose.prod.yml build --no-cache

echo -e "${BLUE}Starting services...${NC}"
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo -e "${BLUE}Waiting for services to be healthy...${NC}"
sleep 10

# Check health
echo -e "${BLUE}Checking service health...${NC}"
docker compose -f docker-compose.prod.yml ps

# Run database migrations
echo -e "${BLUE}Running database migrations...${NC}"
docker compose -f docker-compose.prod.yml exec -T api alembic upgrade head || true

# Seed initial data
echo -e "${BLUE}Seeding initial data...${NC}"
docker compose -f docker-compose.prod.yml exec -T api python -c "
import asyncio
from src.db.seed import run_seed
from src.db.database import async_session_factory
async def main():
    async with async_session_factory() as session:
        await run_seed(session)
asyncio.run(main())
" || true

echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    Deployment Complete!                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Create admin user:"
echo -e "     ${BLUE}docker compose -f docker-compose.prod.yml exec api python -m src.scripts.create_admin${NC}"
echo ""
echo "  2. Access the application:"
echo -e "     ${GREEN}https://${DOMAIN}${NC}"
echo ""
echo "  3. View logs:"
echo -e "     ${BLUE}docker compose -f docker-compose.prod.yml logs -f${NC}"
echo ""
