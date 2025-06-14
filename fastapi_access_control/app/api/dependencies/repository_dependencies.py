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
        """
        Initializes the RepositoryContainer with a session factory.
        
        Args:
            session_factory: A callable that returns a new AsyncSession instance for database operations.
        """
        self.session_factory = session_factory
    
    @lru_cache(maxsize=1)
    def get_card_repository(self) -> CardRepositoryPort:
        """
        Returns a cached instance of the card repository using the configured session factory.
        
        Returns:
            An implementation of CardRepositoryPort backed by SQLAlchemy.
        """
        return SqlAlchemyCardRepository(session_factory=self.session_factory)
    
    @lru_cache(maxsize=1)
    def get_door_repository(self) -> DoorRepositoryPort:
        """
        Returns a cached instance of the door repository using the configured session factory.
        
        Returns:
            An implementation of DoorRepositoryPort backed by SQLAlchemy.
        """
        return SqlAlchemyDoorRepository(session_factory=self.session_factory)
    
    @lru_cache(maxsize=1)
    def get_user_repository(self) -> UserRepositoryPort:
        """
        Returns a cached instance of the user repository using the configured session factory.
        
        Returns:
            An implementation of UserRepositoryPort backed by SQLAlchemy.
        """
        return SqlAlchemyUserRepository(session_factory=self.session_factory)
    
    @lru_cache(maxsize=1)
    def get_permission_repository(self) -> PermissionRepositoryPort:
        """
        Returns a cached instance of the permission repository using the configured session factory.
        """
        return PermissionRepository(session_factory=self.session_factory)
    
    @lru_cache(maxsize=1)
    def get_mqtt_message_service(self) -> MqttMessageService:
        """
        Returns a cached instance of MqttMessageService initialized with a SQLAlchemy-based MQTT message repository.
        """
        mqtt_repository = SqlAlchemyMqttMessageRepository(session_factory=self.session_factory)
        return MqttMessageService(repository=mqtt_repository)


# Global container instance
@lru_cache(maxsize=1)
def get_repository_container() -> RepositoryContainer:
    """
    Returns the global singleton instance of the repository container.
    
    The container provides access to cached repository and service instances using the application's asynchronous session factory.
    """
    return RepositoryContainer(session_factory=AsyncSessionLocal)


# Individual dependency functions for FastAPI
def get_card_repository() -> CardRepositoryPort:
    """
    Provides a singleton CardRepository instance for dependency injection.
    
    Returns:
        A cached CardRepositoryPort instance from the global repository container.
    """
    container = get_repository_container()
    return container.get_card_repository()


def get_door_repository() -> DoorRepositoryPort:
    """
    Provides a cached DoorRepository instance for dependency injection.
    
    Returns:
        An instance of DoorRepositoryPort from the global repository container.
    """
    container = get_repository_container()
    return container.get_door_repository()


def get_user_repository() -> UserRepositoryPort:
    """
    Provides a singleton UserRepository instance for dependency injection.
    
    Returns:
        A cached UserRepositoryPort implementation from the global repository container.
    """
    container = get_repository_container()
    return container.get_user_repository()


def get_permission_repository() -> PermissionRepositoryPort:
    """
    Provides a cached PermissionRepository instance for dependency injection.
    
    Returns:
        A singleton PermissionRepositoryPort instance from the global repository container.
    """
    container = get_repository_container()
    return container.get_permission_repository()


def get_mqtt_message_service() -> MqttMessageService:
    """
    Provides a singleton instance of MqttMessageService for dependency injection.
    
    Returns:
        A cached MqttMessageService instance from the global repository container.
    """
    container = get_repository_container()
    return container.get_mqtt_message_service()