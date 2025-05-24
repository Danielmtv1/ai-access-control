from .mqtt_message import MqttMessage
from ..ports.mqtt_message_repository_port import MqttMessageRepositoryPort
import logging

logger = logging.getLogger(__name__)

class MqttMessageService:
    def __init__(self, repository: MqttMessageRepositoryPort):
        self.repository = repository

    async def process_mqtt_message(self, topic: str, message_payload: str):
        logger.info(f"Domain Service: Processing message on topic {topic}")

        message = MqttMessage(topic=topic, message=message_payload)

        await self.repository.save(message)
        logger.info(f"Domain Service: Message saved to repository.")

    async def get_all_messages(self) -> list[MqttMessage]:
        logger.info("Domain Service: Getting all messages from repository.")
        return await self.repository.get_all()

    # Add other domain methods related to MQTT messages as needed 