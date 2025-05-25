from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class MqttMessageBase(BaseModel):
    """Base schema for MQTT message data"""
    topic: str = Field(..., min_length=1, description="MQTT topic")
    message: str = Field(..., min_length=1, description="Message content")

class MqttMessageCreate(MqttMessageBase):
    """Schema for creating a new MQTT message"""
    pass

class MqttMessageResponse(MqttMessageBase):
    """Schema for MQTT message response"""
    id: int = Field(..., description="Unique message identifier")
    timestamp: datetime = Field(..., description="Message timestamp")
    
    class Config:
        from_attributes = True

class MqttMessageList(BaseModel):
    """Schema for list of MQTT messages"""
    messages: List[MqttMessageResponse]
    total: int 