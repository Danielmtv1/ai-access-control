.PHONY: help build up down ps logs clean db-migrate db-rollback test test-all test-unit test-integration test-coverage

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

# Testing commands
test:
	$(DC) --profile test run --rm test pytest tests/domain/ tests/application/ -v --ignore=tests/test_asyncio_mqtt_adapter.py --ignore=tests/test_sqlalchemy_mqtt_repository.py

test-all:
	$(DC) --profile test run --rm test pytest tests/domain/ tests/application/ tests/integration/ -v --ignore=tests/test_asyncio_mqtt_adapter.py --ignore=tests/test_sqlalchemy_mqtt_repository.py

test-unit:
	$(DC) --profile test run --rm test pytest tests/domain/ tests/application/ -v

test-integration:
	$(DC) --profile test run --rm test pytest tests/integration/ -v

test-coverage:
	$(DC) --profile test run --rm test pytest --cov=app --cov-report=html --cov-report=term-missing tests/domain/ tests/application/ -v

# Cleanup
clean:
	$(DC) down -v
	docker system prune -f

# Help commands
help:
	@echo "Available commands:"
	@echo "  make build          - Rebuild images"
	@echo "  make up            - Start containers"
	@echo "  make down          - Stop containers"
	@echo "  make ps            - List running containers"
	@echo "  make logs          - Show container logs"
	@echo "  make db-migrate    - Run database migrations"
	@echo "  make db-rollback   - Rollback last migration"
	@echo "  make test          - Run unit tests (domain + application)"
	@echo "  make test-all      - Run all tests (unit + integration)"
	@echo "  make test-unit     - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo "  make clean         - Clean containers, volumes and cache"
	@echo "  make dev           - Start containers in development mode"
	@echo "  make restart       - Restart containers" 