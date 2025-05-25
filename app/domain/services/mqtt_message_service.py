from datetime import datetime
import logging
from ..entities.mqtt_message import MqttMessage
from ...ports.repositories.mqtt_message_repository_port import MqttMessageRepositoryPort
from ..exceptions import MqttMessageProcessingError

logger = logging.getLogger(__name__)

class MqttMessageService:
    """Domain service for MQTT message processing."""
    
    def __init__(self, repository: MqttMessageRepositoryPort):
        """Initialize the service with a repository."""
        self._repository = repository
    
    async def process_message(self, topic: str, payload: str) -> MqttMessage:
        """Process an MQTT message."""
        logger.info(f"Processing message on topic {topic}")
        
        # Create domain entity
        message = MqttMessage(
            id=None,  # Will be assigned when saved
            topic=topic,
            message=payload,
            timestamp=datetime.utcnow()
        )
        
        # Validate message
        if not message.is_valid():
            raise MqttMessageProcessingError("Invalid message")
        
        # Save message
        saved_message = await self._repository.save(message)
        logger.info(f"Message saved with ID: {saved_message.id}")
        
        return saved_message
    
    async def get_all_messages(self) -> list[MqttMessage]:
        """Get all messages."""
        logger.info("Getting all messages")
        return await self._repository.get_all() 