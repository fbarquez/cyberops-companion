# IR Companion - Makefile
# Common commands for development and deployment

.PHONY: help dev prod build up down logs clean test migrate shell db-shell

# Default target
help:
	@echo "IR Companion - Available Commands"
	@echo "================================="
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start development environment"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make logs         - View logs (all services)"
	@echo "  make logs-api     - View API logs"
	@echo "  make logs-web     - View Web logs"
	@echo "  make build        - Build all containers"
	@echo "  make rebuild      - Rebuild without cache"
	@echo ""
	@echo "Production:"
	@echo "  make prod         - Start production environment"
	@echo "  make prod-down    - Stop production environment"
	@echo ""
	@echo "Database:"
	@echo "  make migrate      - Run database migrations"
	@echo "  make db-shell     - Open PostgreSQL shell"
	@echo "  make db-backup    - Backup database"
	@echo "  make db-restore   - Restore database from backup"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests"
	@echo "  make test-api     - Run API tests"
	@echo "  make test-web     - Run Web tests"
	@echo ""
	@echo "Utilities:"
	@echo "  make shell-api    - Open shell in API container"
	@echo "  make shell-web    - Open shell in Web container"
	@echo "  make clean        - Remove containers and volumes"
	@echo "  make status       - Show container status"

# Development
dev:
	docker compose up -d
	@echo "Development environment started"
	@echo "API: http://localhost:8000"
	@echo "Web: http://localhost:3000"
	@echo "API Docs: http://localhost:8000/docs"

# Development with hot reload
dev-hot:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "Development environment with hot reload started"
	@echo "API: http://localhost:8000 (hot reload enabled)"
	@echo "Web: http://localhost:3000 (hot reload enabled)"
	@echo "API Docs: http://localhost:8000/docs"

dev-hot-down:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

rebuild:
	docker compose build --no-cache

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-web:
	docker compose logs -f web

# Production
prod:
	docker compose -f docker-compose.prod.yml up -d
	@echo "Production environment started"

prod-down:
	docker compose -f docker-compose.prod.yml down

prod-build:
	docker compose -f docker-compose.prod.yml build

# Database
migrate:
	docker compose exec api alembic upgrade head

db-shell:
	docker compose exec db psql -U postgres -d ir_companion

db-backup:
	@mkdir -p backups
	docker compose exec db pg_dump -U postgres ir_companion > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup created in backups/"

db-restore:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make db-restore FILE=backups/backup_file.sql"; \
		exit 1; \
	fi
	docker compose exec -T db psql -U postgres ir_companion < $(FILE)
	@echo "Database restored from $(FILE)"

# Testing
test: test-api test-web

test-api:
	docker compose exec api pytest tests/ -v --cov=src --cov-report=term-missing

test-web:
	docker compose exec web npm test

test-e2e:
	docker compose exec web npm run test:e2e

# Shells
shell-api:
	docker compose exec api /bin/bash

shell-web:
	docker compose exec web /bin/sh

# Redis shell
redis-shell:
	docker compose exec redis redis-cli

# Utilities
clean:
	docker compose down -v --remove-orphans
	docker system prune -f
	@echo "Cleaned up containers and volumes"

status:
	docker compose ps

# Health checks
health:
	@echo "Checking service health..."
	@curl -sf http://localhost:8000/health && echo "API: OK" || echo "API: FAILED"
	@curl -sf http://localhost:3000 > /dev/null && echo "Web: OK" || echo "Web: FAILED"

# Install dependencies locally (for IDE support)
install-local:
	cd apps/api && pip install -r requirements.txt
	cd apps/web && npm install

# Format code
format:
	cd apps/api && black src/ tests/
	cd apps/api && isort src/ tests/
	cd apps/web && npm run format

# Lint
lint:
	cd apps/api && ruff check src/ tests/
	cd apps/web && npm run lint

# Generate secrets
secrets:
	@echo "JWT_SECRET=$$(openssl rand -hex 32)"
	@echo "SECRET_KEY=$$(openssl rand -hex 32)"
