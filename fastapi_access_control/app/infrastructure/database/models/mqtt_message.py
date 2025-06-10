from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from app.shared.database.base import Base
import uuid

class MqttMessageModel(Base):
    """Modelo de base de datos para mensajes MQTT"""
    
    __tablename__ = "mqtt_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    topic = Column(String, index=True, nullable=False)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<MqttMessage(id={self.id}, topic='{self.topic}', timestamp='{self.timestamp}')>" 