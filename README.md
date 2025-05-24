# FastAPI Access Control System

Access control system based on FastAPI that implements a hexagonal architecture (ports and adapters) for managing access, users, devices, and doors.

## Features

- User and role management (Planned)
- Access control and permissions (Planned)
- MQTT device integration
- Logging and audit system (Basic logging implemented)
- Real-time monitoring (Planned)
- JWT authentication (Planned)
- RESTful API
- Database integration (Asynchronous SQLAlchemy implemented)
- Docker support
- Robust error handling
- Centralized configuration with Pydantic Settings

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
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration (DATABASE_URL, MQTT settings)
```

5. Run database migrations:
```bash
# Make sure your database server is running and DATABASE_URL is set correctly in .env
cd fastapi_access_control
alembic upgrade head
cd ..
```

6. Start the application:
```bash
# Ensure you are in the project root directory
uvicorn fastapi_access_control.app.main:app --reload
# Or using the Makefile
# make dev
```

## Documentation

API documentation will be available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
.
├── fastapi_access_control/  # Main application source code
│   ├── app/
│   │   ├── adapters/    # Implementations of ports (messaging, persistence, etc.)
│   │   ├── domain/      # Business logic, entities, ports
│   │   ├── infrastructure/  # Lower-level infrastructure details (DB engine, etc.)
│   │   ├── api/         # API endpoints
│   │   └── main.py      # Application entry point and dependency injection setup
│   ├── alembic/       # Database migrations
│   ├── tests/         # Test files
│   └── ...
├── .env.example       # Example environment variables
├── requirements.txt   # Project dependencies
├── README.md          # This file
├── Makefile           # Project commands
└── ...
```

## License

This project is under the MIT License. See the `LICENSE` file for more details. 