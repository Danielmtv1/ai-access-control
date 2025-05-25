from dataclasses import dataclass
from app.domain.services.mqtt_message_service import MqttMessageService
from app.domain.entities.mqtt_message import MqttMessage

@dataclass(frozen=True)
class ProcessMqttMessageCommand:
    topic: str
    payload: str

class ProcessMqttMessageUseCase:
    """Use case para procesar mensajes MQTT"""
    
    def __init__(self, mqtt_service: MqttMessageService):
        self._mqtt_service = mqtt_service
    
    async def execute(self, command: ProcessMqttMessageCommand) -> MqttMessage:
        """Procesa un mensaje MQTT"""
        return await self._mqtt_service.process_message(
            command.topic, 
            command.payload
        ) 