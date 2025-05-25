from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.domain.entities.mqtt_message import MqttMessage
from app.domain.exceptions import RepositoryError
from app.ports.mqtt_message_repository_port import MqttMessageRepositoryPort
from app.infrastructure.database.models.mqtt_message import MqttMessageModel

class SqlAlchemyMqttMessageRepository(MqttMessageRepositoryPort):
    """Implementación del repositorio de mensajes MQTT usando SQLAlchemy"""
    
    def __init__(self, session_factory):
        self._session_factory = session_factory
    
    async def save(self, message: MqttMessage) -> None:
        """Guarda un mensaje MQTT en la base de datos"""
        try:
            async with self._session_factory() as session:
                db_message = MqttMessageModel(
                    topic=message.topic,
                    message=message.message,
                    timestamp=message.timestamp
                )
                session.add(db_message)
                await session.commit()
        except SQLAlchemyError as e:
            raise RepositoryError(f"Error al guardar mensaje MQTT: {str(e)}") from e
    
    async def get_all(self) -> List[MqttMessage]:
        """Obtiene todos los mensajes MQTT"""
        try:
            async with self._session_factory() as session:
                result = await session.execute(select(MqttMessageModel))
                db_messages = result.scalars().all()
                return [
                    MqttMessage(
                        id=msg.id,
                        topic=msg.topic,
                        message=msg.message,
                        timestamp=msg.timestamp
                    )
                    for msg in db_messages
                ]
        except SQLAlchemyError as e:
            raise RepositoryError(f"Error al obtener mensajes MQTT: {str(e)}") from e
    
    async def get_by_topic(self, topic: str) -> List[MqttMessage]:
        """Obtiene mensajes MQTT por tema"""
        try:
            async with self._session_factory() as session:
                query = select(MqttMessageModel).where(MqttMessageModel.topic == topic)
                result = await session.execute(query)
                db_messages = result.scalars().all()
                return [
                    MqttMessage(
                        id=msg.id,
                        topic=msg.topic,
                        message=msg.message,
                        timestamp=msg.timestamp
                    )
                    for msg in db_messages
                ]
        except SQLAlchemyError as e:
            raise RepositoryError(f"Error al obtener mensajes MQTT por tema: {str(e)}") from e
    
    async def get_by_id(self, message_id: int) -> Optional[MqttMessage]:
        """Obtiene un mensaje MQTT por su ID"""
        try:
            async with self._session_factory() as session:
                query = select(MqttMessageModel).where(MqttMessageModel.id == message_id)
                result = await session.execute(query)
                db_message = result.scalar_one_or_none()
                
                if db_message:
                    return MqttMessage(
                        id=db_message.id,
                        topic=db_message.topic,
                        message=db_message.message,
                        timestamp=db_message.timestamp
                    )
                return None
        except SQLAlchemyError as e:
            raise RepositoryError(f"Error al obtener mensaje MQTT por ID: {str(e)}") from e

    # Implement other methods from MqttMessageRepositoryPort 