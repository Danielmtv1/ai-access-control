from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import asyncio
import time
from datetime import datetime

from app.infrastructure.observability.metrics import (
    mqtt_connection_status, 
    db_connections,
    active_sessions
)
from app.shared.database import AsyncSessionLocal

router = APIRouter()

class HealthStatus(BaseModel):
    status: str
    timestamp: datetime
    version: str
    checks: Dict[str, Any]

class DetailedHealthCheck(BaseModel):
    status: str
    response_time_ms: float
    details: Dict[str, Any]

async def check_database() -> DetailedHealthCheck:
    """Check database connectivity"""
    start_time = time.time()
    
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            
        response_time = (time.time() - start_time) * 1000
        
        return DetailedHealthCheck(
            status="healthy",
            response_time_ms=response_time,
            details={
                "connection_pool": "active",
                "query_test": "passed"
            }
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return DetailedHealthCheck(
            status="unhealthy", 
            response_time_ms=response_time,
            details={"error": str(e)}
        )

async def check_mqtt() -> DetailedHealthCheck:
    """Check MQTT connectivity"""
    start_time = time.time()
    
    try:
        # Check connection status from metrics
        connection_value = mqtt_connection_status._value._value
        is_connected = connection_value == 1
        
        response_time = (time.time() - start_time) * 1000
        
        return DetailedHealthCheck(
            status="healthy" if is_connected else "unhealthy",
            response_time_ms=response_time,
            details={
                "connected": is_connected,
                "broker": "mqtt:1883"
            }
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return DetailedHealthCheck(
            status="unhealthy",
            response_time_ms=response_time, 
            details={"error": str(e)}
        )

@router.get("/health", response_model=HealthStatus)
async def health_check():
    """Basic health check endpoint"""
    return HealthStatus(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        checks={}
    )

@router.get("/health/detailed", response_model=HealthStatus)
async def detailed_health_check():
    """Detailed health check with all services"""
    
    # Run all checks concurrently
    db_check, mqtt_check = await asyncio.gather(
        check_database(),
        check_mqtt(),
        return_exceptions=True
    )
    
    # Determine overall status
    all_healthy = all([
        getattr(db_check, 'status', 'unhealthy') == 'healthy',
        getattr(mqtt_check, 'status', 'unhealthy') == 'healthy'
    ])
    
    overall_status = "healthy" if all_healthy else "degraded"
    
    return HealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        checks={
            "database": db_check.dict() if hasattr(db_check, 'dict') else {"status": "error"},
            "mqtt": mqtt_check.dict() if hasattr(mqtt_check, 'dict') else {"status": "error"}
        }
    )

@router.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi import Response
    
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    ) 