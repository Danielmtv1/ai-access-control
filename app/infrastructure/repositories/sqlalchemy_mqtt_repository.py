from typing import List, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from app.domain.entities.mqtt_message import MqttMessage
from app.ports.mqtt_message_repository_port import MqttMessageRepositoryPort
from app.infrastructure.persistence.mappers.mqtt_message_mapper import MqttMessageMapper
from app.infrastructure.persistence.models.mqtt_message_model import MqttMessageModel
from app.domain.exceptions import RepositoryError
import logging

logger = logging.getLogger(__name__)

class SqlAlchemyMqttRepository(MqttMessageRepositoryPort):
    """Implementación del repositorio de mensajes MQTT usando SQLAlchemy"""
    
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self._session_factory = session_factory
        self._mapper = MqttMessageMapper()
    
    async def save(self, message: MqttMessage) -> MqttMessage:
        """Guarda un mensaje MQTT en la base de datos"""
        async with self._session_factory() as session:
            try:
                model = self._mapper.to_model(message)
                session.add(model)
                await session.commit()
                await session.refresh(model)
                return self._mapper.to_domain(model)
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Error de base de datos al guardar mensaje MQTT: {e}")
                raise RepositoryError(f"Error al guardar mensaje MQTT: {e}") from e
            except Exception as e:
                await session.rollback()
                logger.error(f"Error inesperado al guardar mensaje MQTT: {e}")
                raise RepositoryError(f"Error inesperado al guardar mensaje MQTT: {e}") from e
    
    async def get_all(self) -> List[MqttMessage]:
        """Obtiene todos los mensajes MQTT de la base de datos"""
        async with self._session_factory() as session:
            try:
                result = await session.execute(select(MqttMessageModel))
                models = result.scalars().all()
                return [self._mapper.to_domain(model) for model in models]
            except SQLAlchemyError as e:
                logger.error(f"Error de base de datos al obtener mensajes MQTT: {e}")
                raise RepositoryError(f"Error al obtener mensajes MQTT: {e}") from e
            except Exception as e:
                logger.error(f"Error inesperado al obtener mensajes MQTT: {e}")
                raise RepositoryError(f"Error inesperado al obtener mensajes MQTT: {e}") from e 