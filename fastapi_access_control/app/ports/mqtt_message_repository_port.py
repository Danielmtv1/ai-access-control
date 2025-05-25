from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.mqtt_message import MqttMessage

class MqttMessageRepositoryPort(ABC):
    @abstractmethod
    async def save(self, message: MqttMessage) -> MqttMessage:
        """
        Saves an MQTT message to the repository.
        """
        pass

    @abstractmethod
    async def get_all(self) -> list[MqttMessage]:
        """
        Retrieves all MQTT messages from the repository.
        """
        pass

    # Add other repository methods as needed
 