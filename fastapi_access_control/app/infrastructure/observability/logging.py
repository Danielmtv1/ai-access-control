import logging
import sys
import json
import uuid
from datetime import datetime, timezone, UTC
from typing import Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

class UUIDEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles UUID objects"""
    def default(self, obj):
        """
        Serializes uuid.UUID objects as strings for JSON encoding.
        
        Returns the string representation of a UUID object, or delegates to the default
        JSON encoder for other types.
        """
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)

class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formats a log record as a JSON string with structured fields.
        
        Includes timestamp, log level, message, module, function name, and line number. Merges any extra fields from the log record and adds exception details if present. Supports serialization of UUID objects.
        """
        log_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        return json.dumps(log_data, cls=UUIDEncoder)

def configure_logging():
    """
    Configures structured JSON logging for the application.
    
    Sets up the root logger with INFO level and a basic text format, elevates specific loggers to DEBUG level, and applies a JSON formatter to all root logger handlers for structured log output.
    """
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)-8s] %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S.%fZ',
        stream=sys.stdout
    )
    
    # Set specific loggers to DEBUG
    logging.getLogger('app.infrastructure.asyncio_mqtt_adapter').setLevel(logging.DEBUG)
    logging.getLogger('aiomqtt').setLevel(logging.DEBUG)
    
    # Apply JSON formatter to root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setFormatter(JsonFormatter())

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger("http")
        
    async def dispatch(self, request: Request, call_next):
        """Log request details and response"""
        start_time = datetime.now(UTC)
        
        # Log request
        self.logger.info(
            "Request started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent")
            }
        )
        
        try:
            response = await call_next(request)
            
            # Log response
            process_time = (datetime.now(UTC) - start_time).total_seconds()
            self.logger.info(
                "Request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": process_time
                }
            )
            
            return response
            
        except Exception as e:
            # Log error
            self.logger.error(
                "Request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

def setup_logging(level: str = "INFO") -> None:
    """Configure application logging"""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JsonFormatter())
    logger.addHandler(console_handler)
    
    # Create file handler
    file_handler = logging.FileHandler("app.log")
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)
    
    # Create HTTP logger
    http_logger = logging.getLogger("http")
    http_logger.setLevel(level)
    http_handler = logging.FileHandler("http.log")
    http_handler.setFormatter(JsonFormatter())
    http_logger.addHandler(http_handler)
    
    # Log startup message
    logger.info(
        "Application started",
        extra={
            "version": "1.0.0",
            "environment": "development"
        }
    ) 