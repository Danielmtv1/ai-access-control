from datetime import datetime, timezone
from typing import Optional

from app.domain.entities.mqtt_message import MqttMessage
from app.infrastructure.database.models.mqtt_message import MqttMessageModel

class MqttMessageMapper:
    """Mapper for converting between MqttMessage domain entity and database model"""
    
    @staticmethod
    def to_domain(model: MqttMessageModel) -> MqttMessage:
        """Convert database model to domain entity"""
        return MqttMessage(
            id=model.id,
            topic=model.topic,
            message=model.message,
            timestamp=model.timestamp
        )
    
    @staticmethod
    def to_model(entity: MqttMessage) -> MqttMessageModel:
        """Convert domain entity to database model"""
        return MqttMessageModel(
            id=entity.id,
            topic=entity.topic,
            message=entity.message,
            timestamp=entity.timestamp
        ) 