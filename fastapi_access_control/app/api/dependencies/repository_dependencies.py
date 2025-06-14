"""
Centralized repository dependency injection.
"""
from functools import lru_cache
from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.database import AsyncSessionLocal
from app.ports.card_repository_port import CardRepositoryPort
from app.ports.door_repository_port import DoorRepositoryPort
from app.ports.user_repository_port import UserRepositoryPort
from app.ports.permission_repository_port import PermissionRepositoryPort
from app.infrastructure.persistence.adapters.card_repository import SqlAlchemyCardRepository
from app.infrastructure.persistence.adapters.door_repository import SqlAlchemyDoorRepository
from app.infrastructure.persistence.adapters.user_repository import SqlAlchemyUserRepository
from app.infrastructure.persistence.adapters.permission_repository import PermissionRepository
from app.infrastructure.persistence.adapters.sqlalchemy_mqtt_repository import SqlAlchemyMqttMessageRepository
from app.domain.services.mqtt_message_service import MqttMessageService


class RepositoryContainer:
    """Container for repository dependencies."""
    
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self.session_factory = session_factory
    
    @lru_cache(maxsize=1)
    def get_card_repository(self) -> CardRepositoryPort:
        return SqlAlchemyCardRepository(session_factory=self.session_factory)
    
    @lru_cache(maxsize=1)
    def get_door_repository(self) -> DoorRepositoryPort:
        return SqlAlchemyDoorRepository(session_factory=self.session_factory)
    
    @lru_cache(maxsize=1)
    def get_user_repository(self) -> UserRepositoryPort:
        return SqlAlchemyUserRepository(session_factory=self.session_factory)
    
    @lru_cache(maxsize=1)
    def get_permission_repository(self) -> PermissionRepositoryPort:
        return PermissionRepository(session_factory=self.session_factory)
    
    @lru_cache(maxsize=1)
    def get_mqtt_message_service(self) -> MqttMessageService:
        mqtt_repository = SqlAlchemyMqttMessageRepository(session_factory=self.session_factory)
        return MqttMessageService(repository=mqtt_repository)


# Global container instance
@lru_cache(maxsize=1)
def get_repository_container() -> RepositoryContainer:
    """Get the global repository container."""
    return RepositoryContainer(session_factory=AsyncSessionLocal)


# Individual dependency functions for FastAPI
def get_card_repository() -> CardRepositoryPort:
    """Dependency to get CardRepository instance."""
    container = get_repository_container()
    return container.get_card_repository()


def get_door_repository() -> DoorRepositoryPort:
    """Dependency to get DoorRepository instance."""
    container = get_repository_container()
    return container.get_door_repository()


def get_user_repository() -> UserRepositoryPort:
    """Dependency to get UserRepository instance."""
    container = get_repository_container()
    return container.get_user_repository()


def get_permission_repository() -> PermissionRepositoryPort:
    """Dependency to get PermissionRepository instance."""
    container = get_repository_container()
    return container.get_permission_repository()


def get_mqtt_message_service() -> MqttMessageService:
    """Dependency to get MqttMessageService instance."""
    container = get_repository_container()
    return container.get_mqtt_message_service()