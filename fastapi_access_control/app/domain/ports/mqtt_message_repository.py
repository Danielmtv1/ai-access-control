from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.mqtt_message import MqttMessage

class MqttMessageRepositoryPort(ABC):
    """Port for MQTT message repository"""
    
    @abstractmethod
    async def save(self, message: MqttMessage) -> MqttMessage:
        """Save a new MQTT message"""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[MqttMessage]:
        """Get all MQTT messages"""
        pass
    
    @abstractmethod
    async def get_by_id(self, message_id: int) -> Optional[MqttMessage]:
        """Get a specific MQTT message by ID"""
        pass
    
    @abstractmethod
    async def get_by_topic(self, topic: str) -> List[MqttMessage]:
        """Get all MQTT messages for a specific topic"""
        pass 