from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

class MqttMessage(BaseModel):
    """Domain entity for MQTT messages"""
    
    topic: str = Field(..., min_length=1, description="MQTT topic")
    message: str = Field(..., min_length=1, description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    id: Optional[int] = Field(None, description="Unique message identifier")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "topic": "test/hello",
                "message": "Hello world",
                "timestamp": "2025-05-25T02:00:00Z"
            }
        }
    )
    
    @field_validator('topic')
    @classmethod
    def validate_topic(cls, v: str) -> str:
        """Validates MQTT topic format"""
        if not v or v.isspace():
            raise ValueError("Topic cannot be empty")
        if '#' in v or '+' in v:
            raise ValueError("Topic cannot contain wildcard characters (# or +)")
        return v.strip()
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validates message content"""
        if not v or v.isspace():
            raise ValueError("Message cannot be empty")
        return v.strip() 