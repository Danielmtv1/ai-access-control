from sqlalchemy import Column, Integer, String, DateTime, func
from app.shared.database.base import Base

class MqttMessageModel(Base):
    """Modelo de base de datos para mensajes MQTT"""
    
    __tablename__ = "mqtt_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True, nullable=False)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<MqttMessage(id={self.id}, topic='{self.topic}', timestamp='{self.timestamp}')>" 