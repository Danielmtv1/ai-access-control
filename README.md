# Access Control System

A FastAPI-based access control system implementing hexagonal architecture and using MQTT for real-time communication.

## 🚀 Features

- 🔐 JWT Authentication with refresh tokens
- 🔄 Hexagonal Architecture (ports & adapters)
- 📡 Real-time MQTT communication
- 📊 Prometheus metrics
- 🏥 Health checks
- 📝 OpenAPI documentation
- 🔍 Structured logging
- 🛡️ Robust security

## 🏗️ Architecture

The system is built following hexagonal architecture principles:

```
fastapi_access_control/
├── app/
│   ├── domain/           # Business logic and rules
│   │   ├── entities/     # Domain entities
│   │   ├── services/     # Domain services
│   │   └── value_objects/# Value objects
│   ├── application/      # Use cases
│   ├── infrastructure/   # External adapters
│   │   ├── persistence/  # Repositories
│   │   ├── mqtt/        # MQTT client
│   │   └── security/    # Security
│   └── api/             # REST API
│       ├── v1/          # v1 endpoints
│       └── schemas/     # Pydantic schemas
```

## 🛠️ Requirements

- Python 3.9+
- PostgreSQL 13+
- MQTT Broker (Mosquitto)
- Docker and Docker Compose (optional)

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/ai-access-control.git
cd ai-access-control
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configurations
```

5. Start with Docker Compose:
```bash
docker-compose up -d
```

## ⚙️ Configuration

### Environment Variables

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/postgres

# MQTT
MQTT_HOST=mqtt
MQTT_PORT=1883
MQTT_USERNAME=optional
MQTT_PASSWORD=optional
USE_TLS=false

# JWT
JWT_SECRET_KEY=your-secret-key
SECRET_KEY=another-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# General
DEBUG=false
```

## 🚀 Usage

### Start the Server

```bash
uvicorn app.main:app --reload
```

### Main Endpoints

- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/auth/refresh` - Token refresh
- `GET /api/v1/mqtt/messages` - Get MQTT messages
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health check
- `GET /metrics` - Prometheus metrics

### API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔐 Authentication

### Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@access-control.com", "password": "AdminPassword123!"}'
```

### Use Token

```bash
curl -X GET "http://localhost:8000/api/v1/protected" \
     -H "Authorization: Bearer <your-token>"
```

## 📊 Monitoring

### Prometheus Metrics

```bash
curl http://localhost:8000/metrics
```

### Health Check

```bash
curl http://localhost:8000/health/detailed
```

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/
```

## 📝 Logging

Logs are automatically configured with the following format:

```json
{
    "timestamp": "2024-03-14T12:00:00Z",
    "level": "INFO",
    "message": "Log message",
    "module": "app.api.v1.auth",
    "function": "login",
    "line": 42
}
```

## 🔄 CI/CD

The project includes GitHub Actions configuration:

- Automated tests
- Linting
- Type checking
- Docker build
- Deployment (configurable)

## 🤝 Contributing

1. Fork the project
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- Your Name - [@your-username](https://github.com/your-username)

## 🙏 Acknowledgments

- FastAPI
- SQLAlchemy
- Pydantic
- aiomqtt
- Prometheus 