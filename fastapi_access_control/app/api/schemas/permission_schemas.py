from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, time
from enum import Enum
from uuid import UUID

class PermissionStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    EXPIRED = "expired"

class CreatePermissionRequest(BaseModel):
    """Request model for creating a new permission"""
    user_id: UUID = Field(
        ...,
        description="ID of the user to grant permission to",
        example="12345678-1234-5678-9012-123456789012"
    )
    door_id: UUID = Field(
        ...,
        description="ID of the door to grant access to",
        example="66666666-7777-8888-9999-000000000000"
    )
    card_id: Optional[UUID] = Field(
        None,
        description="Optional: Specific card ID for card-based permission",
        example="11111111-2222-3333-4444-555555555555"
    )
    valid_from: datetime = Field(
        ...,
        description="Start date and time for the permission",
        example="2024-01-01T09:00:00Z"
    )
    valid_until: Optional[datetime] = Field(
        None,
        description="End date and time for the permission (null for permanent)",
        example="2024-12-31T23:59:59Z"
    )
    access_schedule: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional access schedule (days of week, time ranges)",
        example={
            "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "start_time": "09:00",
            "end_time": "17:00"
        }
    )
    pin_required: bool = Field(
        False,
        description="Whether PIN is required for this permission"
    )

    @validator('valid_until')
    def validate_valid_until(cls, v, values):
        if v and 'valid_from' in values and v <= values['valid_from']:
            raise ValueError('valid_until must be after valid_from')
        return v

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat() if dt else None
        }

class UpdatePermissionRequest(BaseModel):
    """Request model for updating an existing permission"""
    status: Optional[PermissionStatusEnum] = Field(
        None,
        description="New status for the permission"
    )
    valid_from: Optional[datetime] = Field(
        None,
        description="New start date and time for the permission"
    )
    valid_until: Optional[datetime] = Field(
        None,
        description="New end date and time for the permission"
    )
    access_schedule: Optional[Dict[str, Any]] = Field(
        None,
        description="New access schedule"
    )
    pin_required: Optional[bool] = Field(
        None,
        description="Whether PIN is required for this permission"
    )

    @validator('valid_until')
    def validate_valid_until(cls, v, values):
        if v and 'valid_from' in values and values['valid_from'] and v <= values['valid_from']:
            raise ValueError('valid_until must be after valid_from')
        return v

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat() if dt else None
        }

class PermissionResponse(BaseModel):
    """Response model for permission data"""
    id: UUID = Field(..., description="Permission ID")
    user_id: UUID = Field(..., description="User ID")
    door_id: UUID = Field(..., description="Door ID")
    card_id: Optional[UUID] = Field(None, description="Card ID (if card-specific)")
    status: PermissionStatusEnum = Field(..., description="Permission status")
    valid_from: datetime = Field(..., description="Permission start date/time")
    valid_until: Optional[datetime] = Field(None, description="Permission end date/time")
    access_schedule: Optional[Dict[str, Any]] = Field(None, description="Access schedule")
    pin_required: bool = Field(..., description="Whether PIN is required")
    created_by: UUID = Field(..., description="ID of user who created this permission")
    last_used: Optional[datetime] = Field(None, description="Last time this permission was used")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat() if dt else None
        }

class PermissionWithDetails(PermissionResponse):
    """Extended permission response with related entity details"""
    user_name: Optional[str] = Field(None, description="User full name")
    user_email: Optional[str] = Field(None, description="User email")
    door_name: Optional[str] = Field(None, description="Door name")
    door_location: Optional[str] = Field(None, description="Door location")
    card_id_string: Optional[str] = Field(None, description="Card identifier string")

class PermissionListResponse(BaseModel):
    """Response model for paginated permission list"""
    permissions: List[PermissionWithDetails] = Field(..., description="List of permissions")
    total: int = Field(..., description="Total number of permissions")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of permissions per page")
    pages: int = Field(..., description="Total number of pages")

class PermissionFilters(BaseModel):
    """Query parameters for filtering permissions"""
    user_id: Optional[UUID] = Field(None, description="Filter by user ID")
    door_id: Optional[UUID] = Field(None, description="Filter by door ID")
    card_id: Optional[UUID] = Field(None, description="Filter by card ID")
    status: Optional[PermissionStatusEnum] = Field(None, description="Filter by status")
    created_by: Optional[UUID] = Field(None, description="Filter by creator")
    valid_only: Optional[bool] = Field(None, description="Show only currently valid permissions")
    expired_only: Optional[bool] = Field(None, description="Show only expired permissions")

class BulkPermissionRequest(BaseModel):
    """Request model for creating multiple permissions"""
    permissions: List[CreatePermissionRequest] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of permissions to create (max 100)"
    )

class BulkPermissionResponse(BaseModel):
    """Response model for bulk permission operations"""
    created: List[PermissionResponse] = Field(..., description="Successfully created permissions")
    failed: List[Dict[str, Any]] = Field(..., description="Failed permission creations with errors")
    total_requested: int = Field(..., description="Total number of permissions requested")
    total_created: int = Field(..., description="Total number of permissions created")
    total_failed: int = Field(..., description="Total number of failed permissions")