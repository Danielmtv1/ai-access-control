from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MqttMessage(Base):
    __tablename__ = "mqtt_messages"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    message = Column(String)
    timestamp = Column(DateTime, server_default=func.now())

    # Uncomment if you want a representation for debugging
    # def __repr__(self):
    #     return f"<MqttMessage(id={self.id}, topic='{self.topic}', message='{self.message[:20]}...', timestamp='{self.timestamp}')>" 