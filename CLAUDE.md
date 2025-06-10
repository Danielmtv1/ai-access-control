# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered Physical Access Control System built with FastAPI that manages access permissions, validates access requests from IoT devices in real-time, and analyzes access patterns with AI to detect anomalies and security threats.

**Core Components:**
- Access control management (users, cards, doors, permissions)  
- Real-time MQTT communication with IoT devices
- JWT-based authentication system
- AI analysis capabilities for security insights
- Clean Architecture with Domain-Driven Design

## Essential Commands

### Development Environment
```bash
# Start all services
make up

# Start in development mode (with build)
make dev

# Stop services
make down

# View logs
make logs

# Restart services
make restart
```

### Database Operations
```bash
# Apply database migrations
make db-migrate

# Rollback last migration
make db-rollback
```

### Testing Commands
```bash
# Run core tests (domain + application)
make test

# Run all tests including integration
make test-all

# Run only unit tests
make test-unit

# Run only integration tests  
make test-integration

# Generate coverage report
make test-coverage
```

### Cleanup
```bash
# Clean containers and volumes
make clean
```

## Architecture Overview

**Clean Architecture Structure:**
- `app/domain/` - Core business logic, entities, and domain services
- `app/application/` - Use cases orchestrating domain operations
- `app/infrastructure/` - External concerns (database, MQTT, persistence)
- `app/api/` - REST API controllers and schemas
- `app/shared/` - Shared utilities and database configuration

**Key Patterns:**
- Repository pattern for data access abstraction
- Domain entities with encapsulated business logic
- Port/Adapter pattern for external integrations
- Dependency injection through FastAPI's dependency system

**Database Models:**
- Users with JWT authentication
- Cards linked to users with activation status
- Doors with security levels and locations
- Permissions linking users/cards to doors with time-based access control
- MQTT message logging for audit trails

**MQTT Integration:**
- Async MQTT client using aiomqtt
- Message processing through domain services
- Bidirectional communication for IoT device validation
- Structured logging of all access events

## Testing Infrastructure

**Test Environment:**
- Isolated Docker Compose test service with dedicated PostgreSQL database
- Async test support with pytest-asyncio
- 82 passing tests with 66% coverage
- Integration tests for complete access control flow

**Required Environment Variables for Tests:**
- `JWT_SECRET_KEY=test_jwt_secret_key_for_testing_only`
- `SECRET_KEY=test_secret_key_for_testing_only`
- `DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres_test`

## Configuration

**Key Environment Variables:**
- `DATABASE_URL` - PostgreSQL connection string
- `MQTT_HOST`, `MQTT_PORT` - MQTT broker configuration
- `JWT_SECRET_KEY`, `SECRET_KEY` - Authentication secrets
- `DEBUG` - Development mode flag
- `ENVIRONMENT` - development/testing/production

**Security Notes:**
- Development secrets auto-generated with `dev_` prefix
- Production requires proper secret keys without `dev_` prefix
- JWT tokens expire in 30 minutes by default
- All MQTT communication is logged for audit

## Current Implementation Status

**Completed Features:**
- Complete card management system with CRUD operations
- Complete door management with access control and security levels  
- Permission system linking users, cards, and doors with scheduling
- Domain entities with business logic encapsulation
- Repository pattern with SQLAlchemy adapters
- Comprehensive testing infrastructure
- JWT authentication system
- MQTT message logging

**In Development:**
- Real-time access validation API for IoT devices
- AI integration for log analysis  
- MQTT bidirectional communication for device responses

## API Structure

**Main Endpoints:**
- `/api/v1/auth/` - Authentication (login, user management)
- `/api/v1/cards/` - Card management operations
- `/api/v1/doors/` - Door management operations  
- `/api/v1/mqtt/` - MQTT message retrieval
- `/health` - Health check endpoint
- `/metrics` - Prometheus metrics

**Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI spec: `http://localhost:8000/openapi.json`