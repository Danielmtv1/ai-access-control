from app.domain.entities.mqtt_message import MqttMessage
from app.infrastructure.persistence.models.mqtt_message_model import MqttMessageModel

class MqttMessageMapper:
    @staticmethod
    def to_domain(model: MqttMessageModel) -> MqttMessage:
        return MqttMessage(
            id=model.id,
            topic=model.topic,
            message=model.message,
            timestamp=model.timestamp
        )
    
    @staticmethod
    def to_model(entity: MqttMessage) -> MqttMessageModel:
        return MqttMessageModel(
            id=entity.id,
            topic=entity.topic,
            message=entity.message,
            timestamp=entity.timestamp
        ) 