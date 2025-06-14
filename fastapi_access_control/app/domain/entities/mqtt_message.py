from dataclasses import dataclass
from datetime import datetime, timezone, UTC
from typing import Optional
from uuid import UUID

@dataclass(frozen=True)
class MqttMessage:
    """Domain entity for MQTT messages"""
    topic: str
    message: str
    timestamp: datetime
    id: Optional[UUID] = None
    
    def __post_init__(self):
        """
        Validates the topic and message fields after initialization.
        
        Raises:
            ValueError: If the topic or message is empty or contains only whitespace, or if the topic contains MQTT wildcard characters (# or +).
        """
        if not self.topic.strip():
            raise ValueError("Topic cannot be empty")
        if not self.message.strip():
            raise ValueError("Message cannot be empty")
        if '#' in self.topic or '+' in self.topic:
            raise ValueError("Topic cannot contain wildcard characters (# or +)")
    
    @classmethod
    def create(cls, topic: str, message: str) -> 'MqttMessage':
        """Factory method to create a new MQTT message"""
        return cls(
            topic=topic.strip(),
            message=message.strip(),
            timestamp=datetime.now(UTC).replace(tzinfo=None),
            id=None
        ) 