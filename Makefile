.PHONY: help build up down ps logs clean db-migrate db-rollback

# Variables
DC = docker-compose -f docker-compose.yml

# Main commands
up:
	$(DC) up -d

down:
	$(DC) down

build:
	$(DC) build

logs:
	$(DC) logs -f

ps:
	$(DC) ps

# Development commands
dev:
	$(DC) up --build

restart:
	$(DC) restart

# Database commands
db-migrate:
	$(DC) exec app alembic upgrade head

db-rollback:
	$(DC) exec app alembic downgrade -1

# Cleanup
clean:
	$(DC) down -v
	docker system prune -f

# Help commands
help:
	@echo "Available commands:"
	@echo "  make build       - Rebuild images"
	@echo "  make up         - Start containers"
	@echo "  make down       - Stop containers"
	@echo "  make ps         - List running containers"
	@echo "  make logs       - Show container logs"
	@echo "  make db-migrate - Run database migrations"
	@echo "  make db-rollback - Rollback last migration"
	@echo "  make clean      - Clean containers, volumes and cache"
	@echo "  make dev        - Start containers in development mode"
	@echo "  make restart    - Restart containers" 