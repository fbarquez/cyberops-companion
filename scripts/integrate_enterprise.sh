#!/bin/bash
# Script to integrate Enterprise features into Community Edition
# This copies enterprise modules and registers them

set -e

COMMUNITY_DIR="/home/fb-user/Desktop/practicas/proyecto/cyberops-companion"
ENTERPRISE_DIR="/home/fb-user/Desktop/practicas/proyecto/cyberops-companion-enterprise"

echo "=========================================="
echo "  ISORA Enterprise Integration"
echo "=========================================="
echo ""

# Check directories exist
if [ ! -d "$ENTERPRISE_DIR" ]; then
    echo "ERROR: Enterprise directory not found at $ENTERPRISE_DIR"
    exit 1
fi

cd "$COMMUNITY_DIR"

echo "[1/6] Copying Backend API files..."
# Models
cp -v "$ENTERPRISE_DIR/apps/api/src/models/bsi_grundschutz.py" "$COMMUNITY_DIR/apps/api/src/models/"
cp -v "$ENTERPRISE_DIR/apps/api/src/models/nis2.py" "$COMMUNITY_DIR/apps/api/src/models/" 2>/dev/null || echo "  - nis2.py not found, skipping"

# Schemas
cp -v "$ENTERPRISE_DIR/apps/api/src/schemas/bsi_grundschutz.py" "$COMMUNITY_DIR/apps/api/src/schemas/"
cp -v "$ENTERPRISE_DIR/apps/api/src/schemas/nis2.py" "$COMMUNITY_DIR/apps/api/src/schemas/" 2>/dev/null || echo "  - nis2.py not found, skipping"

# Services
cp -v "$ENTERPRISE_DIR/apps/api/src/services/bsi_grundschutz_service.py" "$COMMUNITY_DIR/apps/api/src/services/"
cp -v "$ENTERPRISE_DIR/apps/api/src/services/bsi_update_service.py" "$COMMUNITY_DIR/apps/api/src/services/"
cp -v "$ENTERPRISE_DIR/apps/api/src/services/nis2_service.py" "$COMMUNITY_DIR/apps/api/src/services/" 2>/dev/null || echo "  - nis2_service.py not found, skipping"

# API endpoints
cp -v "$ENTERPRISE_DIR/apps/api/src/api/v1/bsi_grundschutz.py" "$COMMUNITY_DIR/apps/api/src/api/v1/"
cp -v "$ENTERPRISE_DIR/apps/api/src/api/v1/nis2.py" "$COMMUNITY_DIR/apps/api/src/api/v1/" 2>/dev/null || echo "  - nis2.py not found, skipping"

# Tasks
cp -v "$ENTERPRISE_DIR/apps/api/src/tasks/bsi_tasks.py" "$COMMUNITY_DIR/apps/api/src/tasks/" 2>/dev/null || echo "  - bsi_tasks.py not found, skipping"

# Migrations
cp -v "$ENTERPRISE_DIR/apps/api/alembic/versions/c3d4e5f6g7h8_add_bsi_grundschutz_tables.py" "$COMMUNITY_DIR/apps/api/alembic/versions/"

# Seed data
cp -v "$ENTERPRISE_DIR/apps/api/src/db/data/bsi_grundschutz_2023.json" "$COMMUNITY_DIR/apps/api/src/db/data/"
cp -v "$ENTERPRISE_DIR/apps/api/src/db/seed_bsi.py" "$COMMUNITY_DIR/apps/api/src/db/"

# PDF Reports
mkdir -p "$COMMUNITY_DIR/apps/api/src/services/pdf_reports/templates"
cp -v "$ENTERPRISE_DIR/apps/api/src/services/pdf_reports/bsi_report_generator.py" "$COMMUNITY_DIR/apps/api/src/services/pdf_reports/" 2>/dev/null || echo "  - bsi_report_generator.py not found"
cp -v "$ENTERPRISE_DIR/apps/api/src/services/pdf_reports/templates/bsi_report.tex" "$COMMUNITY_DIR/apps/api/src/services/pdf_reports/templates/" 2>/dev/null || echo "  - bsi_report.tex not found"

# Copilot (AI)
if [ -d "$ENTERPRISE_DIR/apps/api/src/services/copilot" ]; then
    echo ""
    echo "[1b/6] Copying AI Copilot..."
    mkdir -p "$COMMUNITY_DIR/apps/api/src/services/copilot"
    cp -rv "$ENTERPRISE_DIR/apps/api/src/services/copilot/"* "$COMMUNITY_DIR/apps/api/src/services/copilot/"
    cp -v "$ENTERPRISE_DIR/apps/api/src/api/v1/copilot.py" "$COMMUNITY_DIR/apps/api/src/api/v1/" 2>/dev/null || echo "  - copilot.py not found"
    cp -v "$ENTERPRISE_DIR/apps/api/src/schemas/copilot.py" "$COMMUNITY_DIR/apps/api/src/schemas/" 2>/dev/null || echo "  - copilot schema not found"
fi

echo ""
echo "[2/6] Copying Frontend files..."
# BSI pages
mkdir -p "$COMMUNITY_DIR/apps/web/app/(dashboard)/compliance/bsi"
cp -rv "$ENTERPRISE_DIR/apps/web/app/(dashboard)/compliance/bsi/"* "$COMMUNITY_DIR/apps/web/app/(dashboard)/compliance/bsi/"

# NIS2 pages (if exist)
if [ -d "$ENTERPRISE_DIR/apps/web/app/(dashboard)/compliance/nis2" ]; then
    mkdir -p "$COMMUNITY_DIR/apps/web/app/(dashboard)/compliance/nis2"
    cp -rv "$ENTERPRISE_DIR/apps/web/app/(dashboard)/compliance/nis2/"* "$COMMUNITY_DIR/apps/web/app/(dashboard)/compliance/nis2/"
fi

# Copilot components (if exist)
if [ -d "$ENTERPRISE_DIR/apps/web/components/copilot" ]; then
    mkdir -p "$COMMUNITY_DIR/apps/web/components/copilot"
    cp -rv "$ENTERPRISE_DIR/apps/web/components/copilot/"* "$COMMUNITY_DIR/apps/web/components/copilot/"
fi

# Compliance components (if exist)
if [ -d "$ENTERPRISE_DIR/apps/web/components/compliance" ]; then
    mkdir -p "$COMMUNITY_DIR/apps/web/components/compliance"
    cp -rv "$ENTERPRISE_DIR/apps/web/components/compliance/"* "$COMMUNITY_DIR/apps/web/components/compliance/"
fi

# AI Settings page (if exists)
if [ -d "$ENTERPRISE_DIR/apps/web/app/(dashboard)/settings/ai" ]; then
    mkdir -p "$COMMUNITY_DIR/apps/web/app/(dashboard)/settings/ai"
    cp -rv "$ENTERPRISE_DIR/apps/web/app/(dashboard)/settings/ai/"* "$COMMUNITY_DIR/apps/web/app/(dashboard)/settings/ai/"
fi

echo ""
echo "[3/6] Enterprise files copied successfully!"
echo ""
echo "=========================================="
echo "  MANUAL STEPS REQUIRED"
echo "=========================================="
echo ""
echo "1. Register BSI router in apps/api/src/api/v1/router.py:"
echo "   from src.api.v1 import bsi_grundschutz"
echo "   api_router.include_router(bsi_grundschutz.router, prefix=\"/bsi\", tags=[\"BSI IT-Grundschutz\"])"
echo ""
echo "2. Add BSI to sidebar in apps/web/components/shared/sidebar.tsx"
echo ""
echo "3. Run migrations:"
echo "   docker compose exec api alembic upgrade head"
echo ""
echo "4. Rebuild containers:"
echo "   docker compose build api web"
echo "   docker compose up -d"
echo ""
echo "=========================================="
