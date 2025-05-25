from app.domain.entities.mqtt_message import MqttMessage
from app.infrastructure.persistence.models.mqtt_message_model import MqttMessageModel

class MqttMessageMapper:
    """Mapper para convertir entre entidad de dominio y modelo de infraestructura"""
    
    @staticmethod
    def to_domain(model: MqttMessageModel) -> MqttMessage:
        """Convierte modelo de infraestructura a entidad de dominio"""
        return MqttMessage(
            id=model.id,
            topic=model.topic,
            message=model.message,
            timestamp=model.timestamp
        )
    
    @staticmethod
    def to_model(entity: MqttMessage) -> MqttMessageModel:
        """Convierte entidad de dominio a modelo de infraestructura"""
        return MqttMessageModel(
            id=entity.id,
            topic=entity.topic,
            message=entity.message,
            timestamp=entity.timestamp
        ) 