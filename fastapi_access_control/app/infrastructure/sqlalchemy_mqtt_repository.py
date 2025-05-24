from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Callable
from ..domain.mqtt_message import MqttMessage
from ..ports.mqtt_message_repository_port import MqttMessageRepositoryPort
from sqlalchemy.exc import SQLAlchemyError # Catch specific SQLAlchemy errors
import logging
from ..domain.exceptions import RepositoryError

logger = logging.getLogger(__name__)

class SqlAlchemyMqttMessageRepository(MqttMessageRepositoryPort):
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        """
        Initialize repository with session factory.
        
        Args:
            session_factory: Callable that returns AsyncSession instance
        """
        self.session_factory = session_factory

    async def save(self, message: MqttMessage) -> MqttMessage:
        async with self.session_factory() as db:
            try:
                db.add(message)
                await db.commit()
                await db.refresh(message)
                return message
            except SQLAlchemyError as e: # Catch specific SQLAlchemy errors
                await db.rollback()
                logger.error(f"Database error saving MQTT message: {e}") # Log the specific error
                raise RepositoryError(f"Error saving MQTT message: {e}") from e # Raise custom domain exception
            except Exception as e:
                await db.rollback()
                logger.error(f"An unexpected error occurred saving MQTT message: {e}")
                raise RepositoryError(f"Unexpected error saving MQTT message: {e}") from e # Raise custom domain exception

    async def get_all(self) -> List[MqttMessage]:
        async with self.session_factory() as db:
            try:
                result = await db.execute(select(MqttMessage))
                messages = result.scalars().all()
                return list(messages)
            except SQLAlchemyError as e: # Catch specific SQLAlchemy errors
                logger.error(f"Database error retrieving MQTT messages: {e}") # Log the specific error
                raise RepositoryError(f"Error retrieving MQTT messages: {e}") from e # Raise custom domain exception
            except Exception as e:
                logger.error(f"An unexpected error occurred retrieving MQTT messages: {e}")
                raise RepositoryError(f"Unexpected error retrieving MQTT messages: {e}") from e # Raise custom domain exception

    # Implement other methods from MqttMessageRepositoryPort 