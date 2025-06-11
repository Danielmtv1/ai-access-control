"""
Access validation API schemas.
"""
from datetime import datetime, timezone
from typing import Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class AccessValidationRequest(BaseModel):
    """Request schema for access validation."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "card_id": "ABC123",
                "door_id": UUID("06191358-d041-4a45-9c68-b324f566e340"),
                "pin": "1234",
                "device_id": "door_lock_001"
            }
        }
    )
    
    card_id: str = Field(
        ..., 
        description="Physical card identifier",
        min_length=1,
        max_length=50
    )
    door_id: UUID = Field(
        ..., 
        description="Door ID to access"
    )
    pin: Optional[str] = Field(
        None, 
        description="PIN code if required for high-security doors",
        min_length=4,
        max_length=8
    )
    device_id: Optional[str] = Field(
        None,
        description="Device identifier for MQTT communication",
        min_length=1,
        max_length=100
    )


class AccessValidationResponse(BaseModel):
    """Response schema for access validation."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_granted": True,
                "reason": "Access granted for John Doe",
                "door_name": "Main Entrance",
                "user_name": "John Doe",
                "card_type": "employee",
                "requires_pin": False,
                "valid_until": "18:00",
                "timestamp": "2024-01-15T09:00:00Z"
            }
        }
    )
    
    access_granted: bool = Field(
        ..., 
        description="Whether access is granted or denied"
    )
    reason: str = Field(
        ..., 
        description="Detailed reason for access decision"
    )
    door_name: str = Field(
        ..., 
        description="Name of the door being accessed"
    )
    user_name: Optional[str] = Field(
        None, 
        description="Name of the card holder"
    )
    card_type: str = Field(
        ..., 
        description="Type of card (employee, visitor, master, etc.)"
    )
    requires_pin: bool = Field(
        ..., 
        description="Whether this door requires PIN authentication"
    )
    valid_until: Optional[str] = Field(
        None, 
        description="Time until which access is valid (HH:MM format)"
    )
    timestamp: datetime = Field(
        ..., 
        description="Timestamp of the validation request"
    )


class AccessValidationResult(BaseModel):
    """Internal result model for access validation use case."""
    
    access_granted: bool
    reason: str
    door_name: str
    user_name: Optional[str] = None
    card_type: str
    requires_pin: bool
    valid_until: Optional[str] = None
    card_id: str
    door_id: UUID
    user_id: Optional[Union[int, UUID]] = None