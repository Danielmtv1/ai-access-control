from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.mqtt_message import MqttMessage
from app.domain.ports.mqtt_message_repository import MqttMessageRepositoryPort
from app.domain.exceptions import RepositoryError
import logging

logger = logging.getLogger(__name__)

class MqttMessageServicePort(ABC):
    """Domain port for MQTT message service"""
    
    @abstractmethod
    async def process_mqtt_message(self, topic: str, message: str) -> None:
        """Process a received MQTT message"""
        pass
    
    @abstractmethod
    async def get_all_messages(self) -> List[MqttMessage]:
        """Get all stored MQTT messages"""
        pass
    
    @abstractmethod
    async def get_messages_by_topic(self, topic: str) -> List[MqttMessage]:
        """Get MQTT messages filtered by topic"""
        pass

class MqttMessageService(MqttMessageServicePort):
    """Implementation of MQTT message service"""
    
    def __init__(self, repository: MqttMessageRepositoryPort):
        self.repository = repository

    async def save_message(self, message: MqttMessage) -> MqttMessage:
        """Save a new MQTT message"""
        try:
            return await self.repository.save(message)
        except Exception as e:
            raise RepositoryError(f"Error saving MQTT message: {str(e)}")
    
    async def get_all_messages(self) -> List[MqttMessage]:
        """Get all MQTT messages"""
        try:
            return await self.repository.get_all()
        except Exception as e:
            raise RepositoryError(f"Error retrieving MQTT messages: {str(e)}")
    
    async def get_message_by_id(self, message_id: int) -> Optional[MqttMessage]:
        """Get a specific MQTT message by ID"""
        try:
            return await self.repository.get_by_id(message_id)
        except Exception as e:
            raise RepositoryError(f"Error retrieving MQTT message: {str(e)}")
    
    async def get_messages_by_topic(self, topic: str) -> List[MqttMessage]:
        """Get all MQTT messages for a specific topic"""
        try:
            return await self.repository.get_by_topic(topic)
        except Exception as e:
            raise RepositoryError(f"Error retrieving MQTT messages for topic {topic}: {str(e)}")
    
    async def process_mqtt_message(self, topic: str, message: str) -> None:
        """Process an incoming MQTT message"""
        try:
            # Use the factory method to create a new MQTT message
            mqtt_message = MqttMessage.create(topic=topic, message=message)
            await self.save_message(mqtt_message)
        except Exception as e:
            raise RepositoryError(f"Error processing MQTT message: {str(e)}") 