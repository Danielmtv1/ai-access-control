from abc import ABC, abstractmethod
from typing import List
from ...domain.entities.mqtt_message import MqttMessage


class MqttMessageRepositoryPort(ABC):
    """Repository port for MQTT messages."""

    @abstractmethod
    async def save(self, message: MqttMessage) -> MqttMessage:
        """Save an MQTT message to the repository."""
        pass

    @abstractmethod
    async def get_all(self) -> List[MqttMessage]:
        """Get all MQTT messages from the repository."""
        pass 