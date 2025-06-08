import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

# Internal imports
from app.config import get_settings
from app.shared.database import AsyncSessionLocal, engine
from app.domain.exceptions import DomainError, RepositoryError, MqttAdapterError

# Infrastructure imports
from app.infrastructure.mqtt.adapters.asyncio_mqtt_adapter import AiomqttAdapter
from app.infrastructure.persistence.adapters.sqlalchemy_mqtt_repository import SqlAlchemyMqttMessageRepository
from app.infrastructure.observability.logging import configure_logging, get_logger
from app.infrastructure.observability.metrics import (
    mqtt_connection_status, 
    app_info,
    api_requests,
    api_request_duration
)

# API imports
from app.api.mqtt import router as mqtt_router
from app.api.v1.auth import router as auth_router
from app.api.v1.cards import router as cards_router
from app.api.v1.doors import router as doors_router
from app.api.health import router as health_router

# Domain services
from app.domain.services.mqtt_message_service import MqttMessageService

# Middleware imports
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.cors_security import add_security_middleware

# Configure structured logging
configure_logging()
logger = get_logger(__name__)

class ApplicationState:
    """Application state container for dependency injection"""
    
    def __init__(self):
        self.mqtt_message_service: MqttMessageService = None
        self.mqtt_adapter: AiomqttAdapter = None
        self.mqtt_task: asyncio.Task = None
        self.settings = get_settings()
        
    async def initialize(self):
        """Initialize all application dependencies"""
        logger.info("Initializing application dependencies...")
        
        # Database session factory
        def db_session_factory():
            return AsyncSessionLocal()
        
        # Repository setup
        mqtt_repository = SqlAlchemyMqttMessageRepository(
            session_factory=db_session_factory
        )
        
        # Domain service setup
        self.mqtt_message_service = MqttMessageService(repository=mqtt_repository)
        
        # Log MQTT configuration
        logger.info("MQTT Configuration:", extra={
            "host": self.settings.MQTT_HOST,
            "port": self.settings.MQTT_PORT,
            "use_tls": self.settings.USE_TLS,
            "username": "configured" if self.settings.MQTT_USERNAME else "not configured",
            "password": "configured" if self.settings.MQTT_PASSWORD else "not configured"
        })
        
        # MQTT adapter setup with improved error handling
        self.mqtt_adapter = AiomqttAdapter(
            message_handler=self.mqtt_message_service.process_mqtt_message
        )
        
        logger.info("Application dependencies initialized successfully")
    
    async def start_background_tasks(self):
        """Start all background tasks"""
        logger.info("Starting background tasks...")
        
        # Start MQTT connection task
        self.mqtt_task = asyncio.create_task(
            self._mqtt_connection_wrapper(),
            name="mqtt_connection_task"
        )
        
        # Update metrics
        app_info.info({
            'version': '1.0.0',
            'name': 'access_control_system',
            'environment': 'development' if self.settings.DEBUG else 'production'
        })
        
        logger.info("Background tasks started successfully")
    
    async def _mqtt_connection_wrapper(self):
        """Wrapper for MQTT connection with status tracking"""
        try:
            logger.info("Starting MQTT connection...")
            await self.mqtt_adapter.connect_and_listen()
            mqtt_connection_status.set(1)  # Set to connected
            logger.info("MQTT connection established successfully")
            
            # Subscribe to test topic
            await self.mqtt_adapter.subscribe("test/#")
            logger.info("Subscribed to test topic")
            
        except asyncio.CancelledError:
            logger.info("MQTT connection task cancelled")
            mqtt_connection_status.set(0)  # Set to disconnected
        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            mqtt_connection_status.set(0)  # Set to disconnected
            raise
    
    async def shutdown(self):
        """Clean shutdown of all services"""
        logger.info("Shutting down application...")
        
        if self.mqtt_task and not self.mqtt_task.done():
            logger.info("Cancelling MQTT task...")
            self.mqtt_task.cancel()
            
            try:
                await asyncio.wait_for(self.mqtt_task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("MQTT task did not complete within timeout")
            except asyncio.CancelledError:
                logger.info("MQTT task cancelled successfully")
        
        if self.mqtt_adapter:
            await self.mqtt_adapter.disconnect()
        
        # Close database connections
        await engine.dispose()
        
        logger.info("Application shutdown completed")

# Global application state
app_state = ApplicationState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with proper error handling"""
    
    try:
        # Startup
        logger.info("Starting Access Control System...")
        
        await app_state.initialize()
        await app_state.start_background_tasks()
        
        # Store state in app for access in endpoints
        app.state.mqtt_message_service = app_state.mqtt_message_service
        app.state.mqtt_adapter = app_state.mqtt_adapter
        app.state.app_state = app_state
        
        logger.info("Access Control System started successfully")
        
        yield
        
    except Exception as e:
        logger.error("Failed to start application", error=str(e), exc_info=True)
        raise
    
    finally:
        # Shutdown
        await app_state.shutdown()

def create_application() -> FastAPI:
    """Factory function to create FastAPI application"""
    
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title="Access Control System",
        description="API for access control system with MQTT",
        version="1.0.0",
        lifespan=lifespan,
        docs_url=None,  # Disable default route
        redoc_url=None,  # Disable default route
        openapi_url="/openapi.json"  # Keep OpenAPI route
    )
    
    # Add security middleware
    add_security_middleware(app)
    
    # Exception handlers
    setup_exception_handlers(app)
    
    # Include routers
    setup_routers(app)
    
    # Add metrics endpoint
    setup_metrics_endpoint(app)
    
    # Configure custom documentation
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="API Documentation - Access Control System",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
            swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
            oauth2_redirect_url=None,
            init_oauth={},
            swagger_ui_parameters={
                "defaultModelsExpandDepth": -1,
                "docExpansion": "none",
                "filter": True,
                "syntaxHighlight.theme": "monokai"
            }
        )

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url="/openapi.json",
            title="API Documentation - Access Control System",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
            redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
            with_google_fonts=True
        )
    
    logger.info("FastAPI application created successfully")
    return app

def setup_exception_handlers(app: FastAPI):
    """Setup global exception handlers with proper logging"""
    
    @app.exception_handler(RepositoryError)
    async def repository_exception_handler(request: Request, exc: RepositoryError):
        logger.error(
            "Repository error occurred",
            endpoint=str(request.url.path),
            method=request.method,
            error=str(exc),
            exc_info=True
        )
        
        api_requests.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=500
        ).inc()
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "database_error",
                "message": "A database error occurred",
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(MqttAdapterError)
    async def mqtt_adapter_exception_handler(request: Request, exc: MqttAdapterError):
        logger.error(
            "MQTT adapter error occurred",
            endpoint=str(request.url.path),
            method=request.method,
            error=str(exc),
            exc_info=True
        )
        
        api_requests.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=500
        ).inc()
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "messaging_error",
                "message": "A messaging system error occurred",
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(DomainError)
    async def domain_exception_handler(request: Request, exc: DomainError):
        logger.warning(
            "Domain error occurred",
            endpoint=str(request.url.path),
            method=request.method,
            error=str(exc)
        )
        
        api_requests.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=400
        ).inc()
        
        return JSONResponse(
            status_code=400,
            content={
                "error": "domain_error",
                "message": str(exc),
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unexpected error occurred",
            endpoint=str(request.url.path),
            method=request.method,
            error=str(exc),
            exc_info=True
        )
        
        api_requests.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=500
        ).inc()
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            }
        )

def setup_routers(app: FastAPI):
    """Setup API routers"""
    
    # Health check endpoints (no prefix)
    app.include_router(health_router, tags=["Health"])
    
    # API v1 endpoints
    app.include_router(mqtt_router, prefix="/api/v1", tags=["MQTT"])
    app.include_router(auth_router, prefix="/api/v1", tags=["Authentication"])
    app.include_router(cards_router, prefix="/api/v1", tags=["Cards"])
    app.include_router(doors_router, prefix="/api/v1", tags=["Doors"])
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information"""
        return {
            "name": "Access Control System API",
            "version": "1.0.0",
            "description": "API for access control system with MQTT integration",
            "documentation": {
                "swagger": "/docs",
                "redoc": "/redoc",
                "openapi": "/openapi.json"
            }
        }

def setup_metrics_endpoint(app: FastAPI):
    """Setup Prometheus metrics endpoint"""
    
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        from fastapi import Response
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Create the application instance
app = create_application()

# Development server runner
if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
        access_log=True,
        loop="asyncio"
    )