from pydantic import BaseModel
from datetime import datetime

class MqttMessageSchema(BaseModel):
    """Schema for MQTT messages"""
    id: int | None = None
    topic: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True 