from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_client.openmetrics.exposition import generate_latest
import time
from functools import wraps
from typing import Callable, Any, Dict

# MQTT Metrics
mqtt_messages_received = Counter(
    'mqtt_messages_received_total',
    'Total number of MQTT messages received',
    ['topic', 'status']
)

mqtt_messages_processed = Counter(
    'mqtt_messages_processed_total', 
    'Total number of MQTT messages processed successfully',
    ['topic']
)

mqtt_connection_status = Gauge(
    'mqtt_connection_status',
    'MQTT connection status (1=connected, 0=disconnected)'
)

# API Metrics  
api_requests = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

# Auth Metrics
auth_attempts = Counter(
    'auth_attempts_total',
    'Total authentication attempts',
    ['status']  # success, failed_credentials, failed_inactive
)

active_sessions = Gauge(
    'active_sessions_total',
    'Number of active user sessions'
)

# Database Metrics
db_connections = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

db_query_duration = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['operation']
)

# System Info
app_info = Info('app_info', 'Application information')
app_info.info({
    'version': '1.0.0',
    'name': 'access_control_system'
})

def track_api_request(func):
    """Decorator to track API request metrics"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            response = await func(*args, **kwargs)
            status = response.status_code
        except Exception as e:
            status = 500
            raise e
        finally:
            duration = time.time() - start_time
            api_requests.labels(
                method=func.__name__,
                endpoint=func.__name__,
                status=status
            ).inc()
            api_request_duration.labels(
                method=func.__name__,
                endpoint=func.__name__
            ).observe(duration)
        return response
    return wrapper

def track_mqtt_message(topic: str, qos: int, message_size: int):
    """Track MQTT message metrics"""
    mqtt_messages_received.labels(topic=topic, status="received").inc()
    mqtt_messages_processed.labels(topic=topic).inc()
    mqtt_connection_status.set(1)
    mqtt_messages_received.labels(topic=topic, status="processed").inc()

def track_db_operation(operation: str, table: str, duration: float):
    """Track database operation metrics"""
    db_query_duration.labels(operation=operation).inc()
    db_query_duration.labels(operation=operation).observe(duration)

def track_auth_attempt(status: str):
    """Track authentication attempt metrics"""
    auth_attempts.labels(status=status).inc()

def get_metrics() -> str:
    """Get all metrics in OpenMetrics format"""
    return generate_latest() 