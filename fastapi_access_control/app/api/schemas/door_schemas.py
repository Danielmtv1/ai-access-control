from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, timezone, time
from enum import Enum
from uuid import UUID

class DoorTypeEnum(str, Enum):
    ENTRANCE = "entrance"
    EXIT = "exit"
    BIDIRECTIONAL = "bidirectional"
    EMERGENCY = "emergency"

class SecurityLevelEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DoorStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    EMERGENCY_OPEN = "emergency_open"
    EMERGENCY_LOCKED = "emergency_locked"

class AccessScheduleSchema(BaseModel):
    """Schema for access schedule"""
    days_of_week: List[int] = Field(
        ...,
        description="Days of week when access is allowed (0=Monday, 6=Sunday)",
        example=[0, 1, 2, 3, 4]  # Monday to Friday
    )
    start_time: str = Field(
        ...,
        description="Start time for access (HH:MM format)",
        example="09:00"
    )
    end_time: str = Field(
        ...,
        description="End time for access (HH:MM format)",
        example="18:00"
    )

    @validator('days_of_week')
    def validate_days_of_week(cls, v):
        if not v:
            raise ValueError('days_of_week cannot be empty')
        if not all(0 <= day <= 6 for day in v):
            raise ValueError('days_of_week must contain values between 0 and 6')
        return sorted(list(set(v)))  # Remove duplicates and sort

    @validator('start_time', 'end_time')
    def validate_time_format(cls, v):
        try:
            time_obj = datetime.strptime(v, '%H:%M').time()
            return v
        except ValueError:
            raise ValueError('Time must be in HH:MM format')

    @validator('end_time')
    def validate_end_after_start(cls, v, values):
        if 'start_time' in values:
            start = datetime.strptime(values['start_time'], '%H:%M').time()
            end = datetime.strptime(v, '%H:%M').time()
            if end <= start:
                raise ValueError('end_time must be after start_time')
        return v

    class Config:
        schema_extra = {
            "example": {
                "days_of_week": [0, 1, 2, 3, 4],
                "start_time": "09:00",
                "end_time": "18:00"
            }
        }

class CreateDoorRequest(BaseModel):
    """Request model for creating a new door"""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the door",
        example="Main Entrance"
    )
    location: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Location of the door",
        example="Building A - Ground Floor"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Description of the door",
        example="Main entrance to Building A"
    )
    door_type: DoorTypeEnum = Field(
        ...,
        description="Type of door",
        example=DoorTypeEnum.ENTRANCE
    )
    security_level: SecurityLevelEnum = Field(
        ...,
        description="Security level of the door",
        example=SecurityLevelEnum.MEDIUM
    )
    requires_pin: bool = Field(
        False,
        description="Whether this door requires a PIN in addition to card access",
        example=False
    )
    max_attempts: int = Field(
        3,
        ge=1,
        le=10,
        description="Maximum failed access attempts before lockout",
        example=3
    )
    lockout_duration: int = Field(
        300,
        ge=60,
        le=3600,
        description="Lockout duration in seconds after max failed attempts",
        example=300
    )
    default_schedule: Optional[AccessScheduleSchema] = Field(
        None,
        description="Default access schedule for this door"
    )

    class Config:
        schema_extra = {
            "example": {
                "name": "Main Entrance",
                "location": "Building A - Ground Floor",
                "description": "Main entrance to Building A",
                "door_type": "entrance",
                "security_level": "medium",
                "requires_pin": False,
                "max_attempts": 3,
                "lockout_duration": 300,
                "default_schedule": {
                    "days_of_week": [0, 1, 2, 3, 4],
                    "start_time": "09:00",
                    "end_time": "18:00"
                }
            }
        }

class UpdateDoorRequest(BaseModel):
    """Request model for updating a door"""
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Name of the door"
    )
    location: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Location of the door"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Description of the door"
    )
    door_type: Optional[DoorTypeEnum] = Field(
        None,
        description="Type of door"
    )
    security_level: Optional[SecurityLevelEnum] = Field(
        None,
        description="Security level of the door"
    )
    requires_pin: Optional[bool] = Field(
        None,
        description="Whether this door requires a PIN"
    )
    max_attempts: Optional[int] = Field(
        None,
        ge=1,
        le=10,
        description="Maximum failed access attempts before lockout"
    )
    lockout_duration: Optional[int] = Field(
        None,
        ge=60,
        le=3600,
        description="Lockout duration in seconds"
    )
    default_schedule: Optional[AccessScheduleSchema] = Field(
        None,
        description="Default access schedule for this door"
    )

    class Config:
        schema_extra = {
            "example": {
                "name": "Main Entrance Updated",
                "security_level": "high",
                "requires_pin": True
            }
        }

class DoorStatusRequest(BaseModel):
    """Request model for changing door status"""
    status: DoorStatusEnum = Field(
        ...,
        description="New status for the door",
        example=DoorStatusEnum.ACTIVE
    )

    class Config:
        schema_extra = {
            "example": {
                "status": "active"
            }
        }

class DoorResponse(BaseModel):
    """Response model for door data"""
    id: UUID = Field(..., description="Door database ID", example="06191358-d041-4a45-9c68-b324f566e340")  # ← Cambiar a UUID
    name: str = Field(..., description="Name of the door", example="Main Entrance")
    location: str = Field(..., description="Location of the door", example="Building A - Ground Floor")
    description: Optional[str] = Field(None, description="Description of the door", example="Main entrance to Building A")
    door_type: DoorTypeEnum = Field(..., description="Type of door", example=DoorTypeEnum.ENTRANCE)
    security_level: SecurityLevelEnum = Field(..., description="Security level", example=SecurityLevelEnum.MEDIUM)
    status: DoorStatusEnum = Field(..., description="Current status", example=DoorStatusEnum.ACTIVE)
    requires_pin: bool = Field(..., description="Whether PIN is required", example=False)
    max_attempts: int = Field(..., description="Maximum failed attempts", example=3)
    lockout_duration: int = Field(..., description="Lockout duration in seconds", example=300)
    failed_attempts: int = Field(..., description="Current failed attempts count", example=0)
    locked_until: Optional[datetime] = Field(None, description="Locked until this time", example=None)
    last_access: Optional[datetime] = Field(None, description="Last successful access", example="2024-06-01T10:30:00")
    default_schedule: Optional[AccessScheduleSchema] = Field(None, description="Default access schedule")
    created_at: datetime = Field(..., description="Creation date", example="2024-01-01T00:00:00")
    updated_at: datetime = Field(..., description="Last update date", example="2024-06-01T10:30:00")

    @classmethod
    def from_entity(cls, door) -> 'DoorResponse':
        """Create DoorResponse from Door entity"""
        # Convert schedule if present
        schedule_response = None
        if door.default_schedule:
            schedule_response = AccessScheduleSchema(
                days_of_week=door.default_schedule.days_of_week,
                start_time=door.default_schedule.start_time.strftime('%H:%M'),
                end_time=door.default_schedule.end_time.strftime('%H:%M')
            )
        
        return cls(
            id=door.id,
            name=door.name,
            location=door.location,
            description=door.description,
            door_type=door.door_type,
            security_level=door.security_level,
            status=door.status,
            requires_pin=door.requires_pin,
            max_attempts=door.max_attempts,
            lockout_duration=door.lockout_duration,
            failed_attempts=door.failed_attempts,
            locked_until=door.locked_until,
            last_access=door.last_access,
            default_schedule=schedule_response,
            created_at=door.created_at,
            updated_at=door.updated_at
        )

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "06191358-d041-4a45-9c68-b324f566e340",
                "name": "Main Entrance",
                "location": "Building A - Ground Floor",
                "description": "Main entrance to Building A",
                "door_type": "entrance",
                "security_level": "medium",
                "status": "active",
                "requires_pin": False,
                "max_attempts": 3,
                "lockout_duration": 300,
                "failed_attempts": 0,
                "locked_until": None,
                "last_access": "2024-06-01T10:30:00",
                "default_schedule": {
                    "days_of_week": [0, 1, 2, 3, 4],
                    "start_time": "09:00",
                    "end_time": "18:00"
                },
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-06-01T10:30:00"
            }
        }

class DoorListResponse(BaseModel):
    """Response model for door list"""
    doors: List[DoorResponse] = Field(..., description="List of doors")
    total: int = Field(..., description="Total number of doors", example=100)
    skip: int = Field(..., description="Number of doors skipped", example=0)
    limit: int = Field(..., description="Maximum number of doors returned", example=50)

    class Config:
        schema_extra = {
            "example": {
                "doors": [
                    {
                        "id": "06191358-d041-4a45-9c68-b324f566e340",
                        "name": "Main Entrance",
                        "location": "Building A - Ground Floor",
                        "description": "Main entrance to Building A",
                        "door_type": "entrance",
                        "security_level": "medium",
                        "status": "active",
                        "requires_pin": False,
                        "max_attempts": 3,
                        "lockout_duration": 300,
                        "failed_attempts": 0,
                        "locked_until": None,
                        "last_access": "2024-06-01T10:30:00",
                        "default_schedule": {
                            "days_of_week": [0, 1, 2, 3, 4],
                            "start_time": "09:00",
                            "end_time": "18:00"
                        },
                        "created_at": "2024-01-01T00:00:00",
                        "updated_at": "2024-06-01T10:30:00"
                    }
                ],
                "total": 100,
                "skip": 0,
                "limit": 50
            }
        }