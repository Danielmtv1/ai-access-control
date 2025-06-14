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
        """
        Creates an instance of the entity with the specified attributes.
        
        Subclasses must implement this method to instantiate and return an entity using the provided keyword arguments.
        """
        pass
    
    @classmethod
    @abstractmethod
    def build(cls, **kwargs) -> Dict[str, Any]:
        """
        Builds a dictionary of attributes for an entity without instantiating the entity.
        
        Args:
            **kwargs: Attribute overrides to customize the generated dictionary.
        
        Returns:
            A dictionary containing the attributes for the entity.
        """
        pass
    
    @classmethod
    def generate_uuid(cls, namespace: Optional[str] = None) -> UUID:
        """
        Generates a UUID for testing purposes.
        
        If a namespace is provided, returns a deterministic UUID5 based on the namespace; otherwise, returns a random UUID4.
        """
        if namespace:
            # Use UUID5 for deterministic UUIDs in tests
            import uuid
            return uuid.uuid5(uuid.NAMESPACE_DNS, f"test.{namespace}")
        return uuid4()
    
    @classmethod
    def generate_email(cls, prefix: str = "user") -> str:
        """
        Generates a unique email address for testing purposes.
        
        The email address consists of the given prefix, an underscore, a random 8-character lowercase suffix, and the domain '@test.example.com'.
        """
        random_suffix = ''.join(secrets.choice(string.ascii_lowercase) for _ in range(8))
        return f"{prefix}_{random_suffix}@test.example.com"
    
    @classmethod
    def generate_card_id(cls, prefix: str = "CARD") -> str:
        """
        Generates a unique card ID string with the specified prefix and a random 8-character uppercase alphanumeric suffix.
        
        Args:
            prefix: The prefix to use for the card ID. Defaults to "CARD".
        
        Returns:
            A unique card ID string in the format "{prefix}_{RANDOM_SUFFIX}".
        """
        random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        return f"{prefix}_{random_suffix}"
    
    @classmethod
    def generate_name(cls, first_name: str = "Test", last_name: str = "User") -> str:
        """
        Generates a unique full name string for testing purposes.
        
        The name is composed of the provided first and last names, followed by a random four-letter lowercase suffix with the first letter capitalized to ensure uniqueness.
        """
        random_suffix = ''.join(secrets.choice(string.ascii_lowercase) for _ in range(4))
        return f"{first_name} {last_name} {random_suffix.capitalize()}"
    
    @classmethod
    def current_utc_time(cls) -> datetime:
        """
        Returns the current UTC datetime.
        
        Useful for generating consistent timestamps in test data.
        """
        return datetime.now(timezone.utc)
    
    @classmethod
    def past_time(cls, days: int = 30) -> datetime:
        """
        Returns a UTC datetime representing a time in the past by the specified number of days.
        
        Args:
        	days: Number of days to subtract from the current UTC time. Defaults to 30.
        
        Returns:
        	A datetime object representing the past time.
        """
        from datetime import timedelta
        return cls.current_utc_time() - timedelta(days=days)
    
    @classmethod
    def future_time(cls, days: int = 30) -> datetime:
        """
        Returns a datetime representing a future time offset by the specified number of days from the current UTC time.
        
        Args:
            days: Number of days to add to the current UTC time. Defaults to 30.
        
        Returns:
            A datetime object representing the future time.
        """
        from datetime import timedelta
        return cls.current_utc_time() + timedelta(days=days)
    
    @classmethod
    def merge_kwargs(cls, defaults: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merges a dictionary of default attributes with override values.
        
        Overrides take precedence over defaults for any matching keys.
        
        Args:
            defaults: The base dictionary of default attribute values.
            overrides: A dictionary of attribute values to override defaults.
        
        Returns:
            A new dictionary containing the merged attributes.
        """
        result = defaults.copy()
        result.update(overrides)
        return result


class DatabaseFactory(BaseFactory):
    """Base factory for creating database model instances."""
    
    @classmethod
    @abstractmethod
    def get_model_class(cls) -> Type:
        """Returns the database model class associated with this factory.
        
        This method must be implemented by subclasses to specify which model class should be instantiated by the factory.
        """
        pass
    
    @classmethod
    def create_model(cls, **kwargs) -> Any:
        """
        Creates and returns an instance of the database model class using built attributes.
        
        Keyword arguments override default attributes when constructing the model instance.
        """
        model_class = cls.get_model_class()
        attributes = cls.build(**kwargs)
        return model_class(**attributes)


class EntityFactory(BaseFactory):
    """Base factory for creating domain entity instances."""
    
    @classmethod
    @abstractmethod
    def get_entity_class(cls) -> Type:
        """Returns the domain entity class associated with this factory.
        
        This abstract method must be implemented by subclasses to specify which entity class should be instantiated by the factory.
        """
        pass
    
    @classmethod
    def create_entity(cls, **kwargs) -> Any:
        """
        Creates and returns an instance of the domain entity class using built attributes.
        
        Keyword arguments can be provided to override default attribute values during entity construction.
        """
        entity_class = cls.get_entity_class()
        attributes = cls.build(**kwargs)
        return entity_class(**attributes)