"""
Card factory for creating test card entities and database models.
"""
from typing import Dict, Any, Optional
from uuid import UUID

from app.domain.entities.card import Card, CardStatus, CardType
from app.infrastructure.database.models.card import CardModel
from .base_factory import EntityFactory, DatabaseFactory


class CardFactory(EntityFactory):
    """Factory for creating Card domain entities."""
    
    @classmethod
    def get_entity_class(cls):
        """
        Returns the Card entity class.
        """
        return Card
    
    @classmethod
    def build(cls, **kwargs) -> Dict[str, Any]:
        """
        Builds a dictionary of card attributes with default values for testing or entity creation.
        
        Default values include generated UUIDs for the card and user, a standard card type, active status, a one-year validity period, and current timestamps. Any provided keyword arguments override the defaults.
        """
        defaults = {
            'id': cls.generate_uuid('card'),
            'card_id': cls.generate_card_id('CARD'),
            'user_id': kwargs.get('user_id', cls.generate_uuid('user')),
            'card_type': CardType.STANDARD,
            'status': CardStatus.ACTIVE,
            'valid_from': cls.current_utc_time(),
            'valid_until': cls.future_time(365),  # Valid for 1 year
            'last_used': None,
            'created_at': cls.current_utc_time(),
            'updated_at': cls.current_utc_time()
        }
        return cls.merge_kwargs(defaults, kwargs)
    
    @classmethod
    def create(cls, **kwargs) -> Card:
        """
        Creates a Card domain entity with default or customized attributes.
        
        Additional keyword arguments can be provided to override default values for the card's properties.
        Returns:
            A Card entity instance.
        """
        return cls.create_entity(**kwargs)
    
    @classmethod
    def create_master(cls, **kwargs) -> Card:
        """
        Creates a master card entity with type MASTER and a 10-year validity period.
        
        Additional attributes can be overridden by providing keyword arguments.
        
        Returns:
            A Card instance representing a master card.
        """
        master_defaults = {
            'card_id': cls.generate_card_id('MASTER'),
            'card_type': CardType.MASTER,
            'valid_until': cls.future_time(3650)  # Valid for 10 years
        }
        return cls.create(**cls.merge_kwargs(master_defaults, kwargs))
    
    @classmethod
    def create_temporary(cls, **kwargs) -> Card:
        """
        Creates a temporary card entity with a validity period of one week.
        
        Additional attributes can be overridden by providing keyword arguments.
        """
        temporary_defaults = {
            'card_id': cls.generate_card_id('TEMP'),
            'card_type': CardType.TEMPORARY,
            'valid_until': cls.future_time(7)  # Valid for 1 week
        }
        return cls.create(**cls.merge_kwargs(temporary_defaults, kwargs))
    
    @classmethod
    def create_visitor(cls, **kwargs) -> Card:
        """
        Creates a visitor card entity with default attributes for a visitor card.
        
        Additional attributes can be provided to override the defaults.
        """
        visitor_defaults = {
            'card_id': cls.generate_card_id('VISITOR'),
            'card_type': CardType.VISITOR,
            'valid_until': cls.future_time(1)  # Valid for 1 day
        }
        return cls.create(**cls.merge_kwargs(visitor_defaults, kwargs))
    
    @classmethod
    def create_inactive(cls, **kwargs) -> Card:
        """
        Creates a card entity with inactive status.
        
        Any additional attributes can be provided via keyword arguments to override defaults.
        """
        inactive_defaults = {
            'status': CardStatus.INACTIVE,
            'card_id': cls.generate_card_id('INACTIVE')
        }
        return cls.create(**cls.merge_kwargs(inactive_defaults, kwargs))
    
    @classmethod
    def create_suspended(cls, **kwargs) -> Card:
        """
        Creates a card entity with suspended status.
        
        Any provided keyword arguments override the default suspended attributes.
        Returns:
            A Card instance with status set to SUSPENDED.
        """
        suspended_defaults = {
            'status': CardStatus.SUSPENDED,
            'card_id': cls.generate_card_id('SUSPENDED')
        }
        return cls.create(**cls.merge_kwargs(suspended_defaults, kwargs))
    
    @classmethod
    def create_lost(cls, **kwargs) -> Card:
        """
        Creates a card entity with status set to lost.
        
        Additional attributes can be provided to override the defaults.
        """
        lost_defaults = {
            'status': CardStatus.LOST,
            'card_id': cls.generate_card_id('LOST')
        }
        return cls.create(**cls.merge_kwargs(lost_defaults, kwargs))
    
    @classmethod
    def create_expired(cls, **kwargs) -> Card:
        """
        Creates a card entity with an expiration date set 30 days in the past.
        
        Additional attributes can be provided to override the defaults.
        """
        expired_defaults = {
            'card_id': cls.generate_card_id('EXPIRED'),
            'valid_until': cls.past_time(30)  # Expired 30 days ago
        }
        return cls.create(**cls.merge_kwargs(expired_defaults, kwargs))
    
    @classmethod
    def create_for_user(cls, user_id: UUID, **kwargs) -> Card:
        """
        Creates a card entity associated with the specified user ID.
        
        Args:
            user_id: The UUID of the user to associate with the card.
        
        Returns:
            A Card entity linked to the given user.
        """
        user_defaults = {'user_id': user_id}
        return cls.create(**cls.merge_kwargs(user_defaults, kwargs))


class CardModelFactory(DatabaseFactory):
    """Factory for creating CardModel database instances."""
    
    @classmethod
    def get_model_class(cls):
        """
        Returns the CardModel class associated with this factory.
        """
        return CardModel
    
    @classmethod
    def build(cls, **kwargs) -> Dict[str, Any]:
        """
        Builds a dictionary of card model attributes with default values for testing.
        
        Keyword arguments can be provided to override any default attribute.
        """
        defaults = {
            'id': cls.generate_uuid('card'),
            'card_id': cls.generate_card_id('CARD'),
            'user_id': kwargs.get('user_id', cls.generate_uuid('user')),
            'card_type': 'standard',
            'status': 'active',
            'valid_from': cls.current_utc_time(),
            'valid_until': cls.future_time(365),
            'last_used': None,
            'created_at': cls.current_utc_time(),
            'updated_at': cls.current_utc_time()
        }
        return cls.merge_kwargs(defaults, kwargs)
    
    @classmethod
    def create(cls, **kwargs) -> CardModel:
        """
        Creates a CardModel instance with default or overridden attributes.
        
        Additional keyword arguments can be provided to override default values for the card model fields.
        """
        return cls.create_model(**kwargs)
    
    @classmethod
    def create_master(cls, **kwargs) -> CardModel:
        """
        Creates a CardModel instance representing a master card with a 10-year validity period.
        
        Additional attributes can be overridden by providing keyword arguments.
        """
        master_defaults = {
            'card_id': cls.generate_card_id('MASTER'),
            'card_type': 'master',
            'valid_until': cls.future_time(3650)
        }
        return cls.create(**cls.merge_kwargs(master_defaults, kwargs))
    
    @classmethod
    def create_temporary(cls, **kwargs) -> CardModel:
        """
        Creates a temporary card model with type 'temporary' and a validity period of 7 days.
        
        Additional attributes can be overridden by providing keyword arguments.
        
        Returns:
            A CardModel instance representing a temporary card.
        """
        temporary_defaults = {
            'card_id': cls.generate_card_id('TEMP'),
            'card_type': 'temporary',
            'valid_until': cls.future_time(7)
        }
        return cls.create(**cls.merge_kwargs(temporary_defaults, kwargs))
    
    @classmethod
    def create_inactive(cls, **kwargs) -> CardModel:
        """
        Creates a card model instance with status set to 'inactive'.
        
        Additional attributes can be provided to override the defaults.
        """
        inactive_defaults = {
            'status': 'inactive',
            'card_id': cls.generate_card_id('INACTIVE')
        }
        return cls.create(**cls.merge_kwargs(inactive_defaults, kwargs))
    
    @classmethod
    def create_suspended(cls, **kwargs) -> CardModel:
        """
        Creates a suspended card model instance with status set to 'suspended'.
        
        Additional attributes can be provided to override the defaults.
        """
        suspended_defaults = {
            'status': 'suspended',
            'card_id': cls.generate_card_id('SUSPENDED')
        }
        return cls.create(**cls.merge_kwargs(suspended_defaults, kwargs))
    
    @classmethod
    def create_for_user(cls, user_id: UUID, **kwargs) -> CardModel:
        """
        Creates a CardModel instance associated with the specified user ID.
        
        Args:
            user_id: The UUID of the user to associate with the card model.
        
        Returns:
            A CardModel instance linked to the given user.
        """
        user_defaults = {'user_id': user_id}
        return cls.create(**cls.merge_kwargs(user_defaults, kwargs))
    
    @classmethod
    def create_batch(cls, count: int, **kwargs) -> list[CardModel]:
        """
        Creates a list of card model instances with optional attribute overrides.
        
        Args:
            count: The number of card model instances to create.
        
        Returns:
            A list containing the created CardModel instances.
        """
        return [cls.create(**kwargs) for _ in range(count)]


# Convenience aliases for backward compatibility
create_test_card = CardFactory.create
create_master_card = CardFactory.create_master
create_test_card_model = CardModelFactory.create