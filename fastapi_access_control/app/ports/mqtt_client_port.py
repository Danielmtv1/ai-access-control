import abc

class MqttClientPort(abc.ABC):
    @abc.abstractmethod
    async def connect_and_listen(self, message_handler: callable):
        """
        Connects to the MQTT broker and starts listening for messages.
        When a message is received, it calls the message_handler.
        """
        pass

    @abc.abstractmethod
    async def publish(self, topic: str, payload: str):
        """
        Publishes a message to a specific topic.
        """
        pass

    # Add other MQTT client methods as needed 