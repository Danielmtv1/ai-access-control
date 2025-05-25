from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.domain.entities.mqtt_message import MqttMessage
from app.ports.mqtt_message_repository_port import MqttMessageRepositoryPort
from app.infrastructure.persistence.mappers.mqtt_message_mapper import MqttMessageMapper
from app.infrastructure.database.models.mqtt_message import MqttMessageModel
from app.domain.exceptions import RepositoryError

class SqlAlchemyMqttMessageRepository(MqttMessageRepositoryPort):
    """SQLAlchemy implementation of MqttMessageRepositoryPort"""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    async def save(self, message: MqttMessage) -> MqttMessage:
        """Save MQTT message to database"""
        try:
            async with self.session_factory() as session:
                message_model = MqttMessageMapper.to_model(message)
                session.add(message_model)
                await session.commit()
                await session.refresh(message_model)
                return MqttMessageMapper.to_domain(message_model)
        except Exception as e:
            raise RepositoryError(f"Error saving MQTT message: {str(e)}")
    
    async def get_all(self) -> List[MqttMessage]:
        """Get all MQTT messages"""
        try:
            async with self.session_factory() as session:
                result = await session.execute(
                    select(MqttMessageModel).order_by(desc(MqttMessageModel.timestamp))
                )
                messages = result.scalars().all()
                return [MqttMessageMapper.to_domain(msg) for msg in messages]
        except Exception as e:
            raise RepositoryError(f"Error getting MQTT messages: {str(e)}")
    
    async def get_by_topic(self, topic: str) -> List[MqttMessage]:
        """Get MQTT messages by topic"""
        try:
            async with self.session_factory() as session:
                result = await session.execute(
                    select(MqttMessageModel)
                    .where(MqttMessageModel.topic == topic)
                    .order_by(desc(MqttMessageModel.timestamp))
                )
                messages = result.scalars().all()
                return [MqttMessageMapper.to_domain(msg) for msg in messages]
        except Exception as e:
            raise RepositoryError(f"Error getting MQTT messages by topic: {str(e)}")
    
    async def get_by_id(self, message_id: int) -> Optional[MqttMessage]:
        """Get MQTT message by ID"""
        try:
            async with self.session_factory() as session:
                result = await session.execute(
                    select(MqttMessageModel).where(MqttMessageModel.id == message_id)
                )
                message = result.scalar_one_or_none()
                return MqttMessageMapper.to_domain(message) if message else None
        except Exception as e:
            raise RepositoryError(f"Error getting MQTT message by ID: {str(e)}")

    # Implement other methods from MqttMessageRepositoryPort 