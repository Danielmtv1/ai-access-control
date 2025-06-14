"""
Base factory class providing common functionality for all test data factories.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, TypeVar, Type, Optional
from uuid import UUID, uuid4
import secrets
import string

T = TypeVar('T')


class BaseFactory(ABC):
    """Abstract base factory for creating test entities with consistent patterns."""
    
    @classmethod
    @abstractmethod
    def create(cls, **kwargs) -> Any:
        """Create an entity instance with the given attributes."""
        pass
    
    @classmethod
    @abstractmethod
    def build(cls, **kwargs) -> Dict[str, Any]:
        """Build entity attributes dictionary without creating the entity."""
        pass
    
    @classmethod
    def generate_uuid(cls, namespace: Optional[str] = None) -> UUID:
        """Generate a deterministic UUID for testing."""
        if namespace:
            # Use UUID5 for deterministic UUIDs in tests
            import uuid
            return uuid.uuid5(uuid.NAMESPACE_DNS, f"test.{namespace}")
        return uuid4()
    
    @classmethod
    def generate_email(cls, prefix: str = "user") -> str:
        """Generate a unique test email address."""
        random_suffix = ''.join(secrets.choice(string.ascii_lowercase) for _ in range(8))
        return f"{prefix}_{random_suffix}@test.example.com"
    
    @classmethod
    def generate_card_id(cls, prefix: str = "CARD") -> str:
        """Generate a unique card ID for testing."""
        random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        return f"{prefix}_{random_suffix}"
    
    @classmethod
    def generate_name(cls, first_name: str = "Test", last_name: str = "User") -> str:
        """Generate a full name for testing."""
        random_suffix = ''.join(secrets.choice(string.ascii_lowercase) for _ in range(4))
        return f"{first_name} {last_name} {random_suffix.capitalize()}"
    
    @classmethod
    def current_utc_time(cls) -> datetime:
        """Get current UTC time for consistent timestamp generation."""
        return datetime.now(timezone.utc)
    
    @classmethod
    def past_time(cls, days: int = 30) -> datetime:
        """Generate a past timestamp for testing."""
        from datetime import timedelta
        return cls.current_utc_time() - timedelta(days=days)
    
    @classmethod
    def future_time(cls, days: int = 30) -> datetime:
        """Generate a future timestamp for testing."""
        from datetime import timedelta
        return cls.current_utc_time() + timedelta(days=days)
    
    @classmethod
    def merge_kwargs(cls, defaults: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Merge default attributes with provided overrides."""
        result = defaults.copy()
        result.update(overrides)
        return result


class DatabaseFactory(BaseFactory):
    """Base factory for creating database model instances."""
    
    @classmethod
    @abstractmethod
    def get_model_class(cls) -> Type:
        """Return the database model class this factory creates."""
        pass
    
    @classmethod
    def create_model(cls, **kwargs) -> Any:
        """Create a database model instance."""
        model_class = cls.get_model_class()
        attributes = cls.build(**kwargs)
        return model_class(**attributes)


class EntityFactory(BaseFactory):
    """Base factory for creating domain entity instances."""
    
    @classmethod
    @abstractmethod
    def get_entity_class(cls) -> Type:
        """Return the domain entity class this factory creates."""
        pass
    
    @classmethod
    def create_entity(cls, **kwargs) -> Any:
        """Create a domain entity instance."""
        entity_class = cls.get_entity_class()
        attributes = cls.build(**kwargs)
        return entity_class(**attributes)