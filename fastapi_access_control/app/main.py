import asyncio
import os
import logging
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from .api import mqtt
from contextlib import asynccontextmanager
from app.shared.database import AsyncSessionLocal
from .infrastructure.asyncio_mqtt_adapter import AsyncioMqttAdapter
from .domain.services import MqttMessageService
from fastapi.responses import JSONResponse
from .domain.exceptions import DomainError, RepositoryError, MqttAdapterError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Dependency Injection Setup ---
    def db_session_factory():
        return AsyncSessionLocal()

    from .infrastructure.sqlalchemy_mqtt_repository import SqlAlchemyMqttMessageRepository
    mqtt_message_repository = SqlAlchemyMqttMessageRepository(session_factory=db_session_factory)

    mqtt_message_service = MqttMessageService(repository=mqtt_message_repository)

    mqtt_adapter = AsyncioMqttAdapter(message_handler=mqtt_message_service.process_mqtt_message)

    app.state.mqtt_message_service = mqtt_message_service
    app.state.mqtt_client_adapter = mqtt_adapter

    # --- Startup Logic ---
    logger.info("Starting MQTT background task.")
    mqtt_task = asyncio.create_task(mqtt_adapter.connect_and_listen())
    yield

    # --- Shutdown Logic ---
    logger.info("Shutting down MQTT background task.")
    mqtt_task.cancel()
    try:
        await mqtt_task
    except asyncio.CancelledError:
        logger.info("MQTT background task cancelled cleanly.")

app = FastAPI(
    title="Access Control System",
    description="API for access control management with FastAPI",
    version="1.0.0",
    lifespan=lifespan
)

# Exception Handlers
@app.exception_handler(RepositoryError)
async def repository_exception_handler(request: Request, exc: RepositoryError):
    logger.error(f"Repository error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "A database error occurred."
        },
    )

@app.exception_handler(MqttAdapterError)
async def mqtt_adapter_exception_handler(request: Request, exc: MqttAdapterError):
    logger.error(f"MQTT adapter error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "A messaging system error occurred."
        },
    )

@app.exception_handler(DomainError)
async def domain_exception_handler(request: Request, exc: DomainError):
    logger.error(f"Domain error: {exc}")
    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc)
        }
    )

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mqtt.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Access Control System"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 