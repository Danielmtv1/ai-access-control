"""
Domain constants and business logic values.

This module contains constants that define business rules and domain logic.
These values are typically stable and don't change per environment.
"""
from enum import Enum
from typing import List, Set


class SecurityConstants:
    """Security-related business constants."""
    
    # Security levels that require master access
    CRITICAL_SECURITY_LEVELS: Set[str] = {"HIGH", "CRITICAL"}
    
    # Security levels in order of priority
    SECURITY_LEVEL_PRIORITY: List[str] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class DeviceConstants:
    """Device and IoT related constants."""
    
    # Device health status thresholds
    BATTERY_HEALTHY_THRESHOLD: int = 50
    BATTERY_WARNING_THRESHOLD: int = 30
    BATTERY_LOW_THRESHOLD: int = 20
    BATTERY_CRITICAL_THRESHOLD: int = 10
    
    # Device status categories
    HEALTHY_STATUS_VALUES: Set[str] = {"online", "active", "operational"}
    UNHEALTHY_STATUS_VALUES: Set[str] = {"offline", "error", "maintenance", "fault"}
    
    # Communication timeouts
    DEVICE_RESPONSE_TIMEOUT: int = 30
    DEVICE_PING_TIMEOUT: int = 10


class DoorConstants:
    """Door and access control constants."""
    
    # Door types that require special handling
    HIGH_SECURITY_DOOR_TYPES: Set[str] = {"security", "vault", "server_room"}
    
    # Emergency door statuses
    EMERGENCY_STATUSES: Set[str] = {"emergency_open", "emergency_locked"}
    
    # Statuses that allow access
    ACCESSIBLE_STATUSES: Set[str] = {"active", "emergency_open"}
    
    # Default schedule for 24/7 access
    DEFAULT_24_7_SCHEDULE = {
        'days_of_week': ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
        'start_time': '00:00',
        'end_time': '23:59'
    }


class CardConstants:
    """Card and credential constants."""
    
    # Card types that have special privileges
    PRIVILEGED_CARD_TYPES: Set[str] = {"master", "admin", "maintenance"}
    
    # Card types for temporary access
    TEMPORARY_CARD_TYPES: Set[str] = {"visitor", "temporary", "contractor"}
    
    # Card statuses that allow access
    ACTIVE_CARD_STATUSES: Set[str] = {"active"}
    
    # Card statuses that deny access
    INACTIVE_CARD_STATUSES: Set[str] = {"inactive", "suspended", "lost", "expired"}


class AccessControlConstants:
    """Access control business rules."""
    
    # PIN validation rules
    PIN_MIN_LENGTH: int = 4
    PIN_MAX_LENGTH: int = 8
    PIN_ALLOWED_CHARACTERS: str = "0123456789"
    
    # Time-based access rules
    SCHEDULE_TIME_FORMAT: str = "%H:%M"
    DAY_ABBREVIATIONS: List[str] = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    
    # Access attempt limits
    MAX_FAILED_ATTEMPTS_BEFORE_ALERT: int = 5
    SUSPICIOUS_ACTIVITY_THRESHOLD: int = 10


class MQTTTopicConstants:
    """MQTT topic patterns and prefixes."""
    
    # Topic prefixes
    ACCESS_REQUEST_PREFIX: str = "access"
    DEVICE_STATUS_PREFIX: str = "device"
    COMMAND_PREFIX: str = "command"
    RESPONSE_PREFIX: str = "response"
    EVENT_PREFIX: str = "event"
    
    # Topic patterns
    ACCESS_TOPIC_PATTERN: str = "{prefix}/door_{door_id}/request"
    STATUS_TOPIC_PATTERN: str = "{prefix}/{device_id}/status"
    COMMAND_TOPIC_PATTERN: str = "{prefix}/{device_id}/{command_type}"
    
    # Event types
    CRITICAL_EVENT_TYPES: Set[str] = {"tamper", "forced_entry", "fire_alarm"}
    INFO_EVENT_TYPES: Set[str] = {"door_opened", "door_closed", "maintenance"}


class DatabaseConstants:
    """Database-related constants."""
    
    # Entity ID validation
    UUID_PATTERN: str = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    
    # Soft delete values
    ACTIVE_RECORD_VALUE: bool = True
    DELETED_RECORD_VALUE: bool = False
    
    # Pagination limits
    ABSOLUTE_MAX_PAGE_SIZE: int = 1000
    MINIMUM_PAGE_SIZE: int = 1


class APIConstants:
    """API-related constants."""
    
    # HTTP status codes for business logic
    BUSINESS_ERROR_STATUS: int = 400
    NOT_FOUND_STATUS: int = 404
    CONFLICT_STATUS: int = 409
    UNPROCESSABLE_STATUS: int = 422
    
    # Content types
    JSON_CONTENT_TYPE: str = "application/json"
    FORM_CONTENT_TYPE: str = "application/x-www-form-urlencoded"
    
    # Headers
    AUTHORIZATION_HEADER: str = "Authorization"
    CONTENT_TYPE_HEADER: str = "Content-Type"
    
    # API versioning
    CURRENT_API_VERSION: str = "v1"
    SUPPORTED_API_VERSIONS: List[str] = ["v1"]


class ValidationConstants:
    """Data validation constants."""
    
    # String length limits
    SHORT_STRING_MAX_LENGTH: int = 50
    MEDIUM_STRING_MAX_LENGTH: int = 255
    LONG_STRING_MAX_LENGTH: int = 1000
    
    # Email validation
    EMAIL_MAX_LENGTH: int = 255
    EMAIL_PATTERN: str = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Name validation
    NAME_MIN_LENGTH: int = 1
    NAME_MAX_LENGTH: int = 100
    NAME_PATTERN: str = r'^[a-zA-Z\s\'-]+$'
    
    # Card ID validation
    CARD_ID_MIN_LENGTH: int = 4
    CARD_ID_MAX_LENGTH: int = 50
    CARD_ID_PATTERN: str = r'^[A-Z0-9_-]+$'


# Convenience exports for commonly used constants
__all__ = [
    'SecurityConstants',
    'DeviceConstants', 
    'DoorConstants',
    'CardConstants',
    'AccessControlConstants',
    'MQTTTopicConstants',
    'DatabaseConstants',
    'APIConstants',
    'ValidationConstants'
]