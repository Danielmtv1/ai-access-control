from sqlalchemy import Column, Integer, String, DateTime, func
from app.shared.database.base import Base

class MqttMessage(Base):
    __tablename__ = "mqtt_messages"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    message = Column(String)
    timestamp = Column(DateTime, server_default=func.now())