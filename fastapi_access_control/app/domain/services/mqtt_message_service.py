from abc import ABC, abstractmethod
from typing import List
from app.domain.entities.mqtt_message import MqttMessage
from ...ports.mqtt_message_repository_port import MqttMessageRepositoryPort
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
        self._repository = repository

    async def process_mqtt_message(self, topic: str, message: str) -> None:
        """Process a received MQTT message"""
        logger.info(f"Domain Service: Processing message on topic {topic}")
        mqtt_message = MqttMessage(topic=topic, message=message)
        await self._repository.save(mqtt_message)
        logger.info(f"Domain Service: Message saved to repository.")

    async def get_all_messages(self) -> List[MqttMessage]:
        """Get all stored MQTT messages"""
        logger.info("Domain Service: Getting all messages from repository.")
        return await self._repository.get_all()

    async def get_messages_by_topic(self, topic: str) -> List[MqttMessage]:
        """Get MQTT messages filtered by topic"""
        return await self._repository.get_by_topic(topic) 