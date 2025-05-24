# FastAPI Access Control System

Access control system based on FastAPI that implements a hexagonal architecture (ports and adapters) for managing access, users, devices, and doors.

## Features

- User and role management
- Access control and permissions
- MQTT device integration
- Logging and audit system
- Real-time monitoring
- JWT authentication
- RESTful API
- Database integration
- Docker support

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/fastapi-access-control.git
cd fastapi-access-control
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install poetry
poetry install
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start the application:
```bash
uvicorn app.main:app --reload
```

## Documentation

API documentation will be available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
fastapi_access_control/
├── app/
│   ├── api/         # API endpoints
│   ├── core/        # Core functionality
│   ├── domain/      # Business logic and entities
│   ├── infrastructure/  # External services and adapters
│   └── main.py      # Application entry point
├── tests/           # Test files
└── ...
```

This project is under the MIT License. See the `LICENSE` file for more details. 