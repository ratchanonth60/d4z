.PHONY: up down build logs ps restart clean help shell api-start api-stop db-start db-stop

# Default target
.DEFAULT_GOAL := help

# Variables
COMPOSE = docker-compose -f docker-compose.yml

# Help command
help:
	@echo "Available commands:"
	@echo "  make up [SERVICE=service_name]        - Start all containers or specific service in detached mode"
	@echo "  make down [SERVICE=service_name]      - Stop and remove all containers or specific service"
	@echo "  make build [SERVICE=service_name]     - Build or rebuild all services or specific service"
	@echo "  make logs [SERVICE=service_name]      - View output from all containers or specific service"
	@echo "  make ps                               - List containers"
	@echo "  make restart [SERVICE=service_name]   - Restart all containers or specific service"
	@echo "  make clean                           - Remove all containers and volumes"
	@echo "  make shell [SERVICE=service_name]     - Open shell in specified service container (default: app)"
	@echo ""
	@echo "API and Database Management:"
	@echo "  make api-start                        - Start FastAPI service with lifespan"
	@echo "  make api-stop                         - Stop FastAPI service gracefully"
	@echo "  make db-start                         - Start database service"
	@echo "  make db-stop                          - Stop database service gracefully"
	@echo ""
	@echo "Examples:"
	@echo "  make up SERVICE=db                    - Start only the database service"
	@echo "  make logs SERVICE=app                 - View logs for the app service"
	@echo "  make shell SERVICE=db                 - Open shell in the database container"

# Start containers
up:
	$(COMPOSE) up -d --build $(SERVICE)

# Stop containers
down:
	$(COMPOSE) down $(SERVICE)

# Build containers
build:
	$(COMPOSE) build $(SERVICE)

# View logs
logs:
	$(COMPOSE) logs -f $(SERVICE)

# List containers
ps:
	$(COMPOSE) ps

# Restart containers
restart:
	$(COMPOSE) restart $(SERVICE)

# Clean up containers and volumes
clean:
	$(COMPOSE) down -v

# Open shell in specified container
shell:
	$(COMPOSE) exec $(SERVICE) sh

# API Lifespan Management
api-start:
	$(COMPOSE) up -d --build app
	@echo "FastAPI service started with lifespan management"

api-stop:
	$(COMPOSE) stop app
	@echo "FastAPI service stopped gracefully"

# Database Management
db-start:
	$(COMPOSE) up -d db
	@echo "Database service started"

db-stop:
	$(COMPOSE) stop db
	@echo "Database service stopped gracefully"
