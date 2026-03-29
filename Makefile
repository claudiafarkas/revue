.PHONY: help frontend-install frontend-dev frontend-build backend-install backend-dev backend-run db-up db-down db-logs

FRONTEND_DIR := frontend
FRONTEND_NPM_CACHE := $(CURDIR)/$(FRONTEND_DIR)/.npm-cache
BACKEND_DIR := backend
CONDA_PREFIX := $(CURDIR)/.conda
FRONTEND_PORT ?= 3101
BACKEND_PORT ?= 8011

help:
	@printf "Available targets:\n"
	@printf "  frontend-install  Install frontend dependencies\n"
	@printf "  frontend-dev      Run the Next.js frontend dev server\n"
	@printf "  frontend-build    Build the frontend for production\n"
	@printf "  backend-install   Install backend Python dependencies (active env)\n"
	@printf "  backend-dev       Run the FastAPI backend with reload\n"
	@printf "  backend-run       Run the FastAPI backend without reload\n"
	@printf "  db-up             Start the Revue PostgreSQL container on port 5434\n"
	@printf "  db-down           Stop the Revue PostgreSQL container\n"
	@printf "  db-logs           Tail logs for the Revue PostgreSQL container\n"

frontend-install:
	mkdir -p $(FRONTEND_NPM_CACHE)
	cd $(FRONTEND_DIR) && npm_config_cache="$(FRONTEND_NPM_CACHE)" npm install

frontend-dev:
	mkdir -p $(FRONTEND_NPM_CACHE)
	cd $(FRONTEND_DIR) && npm_config_cache="$(FRONTEND_NPM_CACHE)" npm run dev -- --port $(FRONTEND_PORT)

frontend-build:
	mkdir -p $(FRONTEND_NPM_CACHE)
	cd $(FRONTEND_DIR) && npm_config_cache="$(FRONTEND_NPM_CACHE)" npm run build

backend-install:
	conda run -p $(CONDA_PREFIX) python3 -m pip install -r $(BACKEND_DIR)/requirements.txt

backend-dev:
	cd $(BACKEND_DIR) && conda run -p $(CONDA_PREFIX) uvicorn api.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT)

backend-run:
	cd $(BACKEND_DIR) && conda run -p $(CONDA_PREFIX) uvicorn api.main:app --host 0.0.0.0 --port $(BACKEND_PORT)

db-up:
	docker compose -f infra/docker-compose.yml up -d postgres

db-down:
	docker compose -f infra/docker-compose.yml down

db-logs:
	docker compose -f infra/docker-compose.yml logs -f postgres