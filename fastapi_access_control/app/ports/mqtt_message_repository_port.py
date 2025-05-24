import abc
from ..domain.mqtt_message import MqttMessage

class MqttMessageRepositoryPort(abc.ABC):
    @abc.abstractmethod
    async def save(self, message: MqttMessage) -> MqttMessage:
        """
        Saves an MQTT message to the repository.
        """
        pass

    @abc.abstractmethod
    async def get_all(self) -> list[MqttMessage]:
        """
        Retrieves all MQTT messages from the repository.
        """
        pass

    # Add other repository methods as needed
 