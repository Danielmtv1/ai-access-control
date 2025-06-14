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
        return Card
    
    @classmethod
    def build(cls, **kwargs) -> Dict[str, Any]:
        """Build card attributes with sensible defaults."""
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
        """Create a Card entity."""
        return cls.create_entity(**kwargs)
    
    @classmethod
    def create_master(cls, **kwargs) -> Card:
        """Create a master card."""
        master_defaults = {
            'card_id': cls.generate_card_id('MASTER'),
            'card_type': CardType.MASTER,
            'valid_until': cls.future_time(3650)  # Valid for 10 years
        }
        return cls.create(**cls.merge_kwargs(master_defaults, kwargs))
    
    @classmethod
    def create_temporary(cls, **kwargs) -> Card:
        """Create a temporary card."""
        temporary_defaults = {
            'card_id': cls.generate_card_id('TEMP'),
            'card_type': CardType.TEMPORARY,
            'valid_until': cls.future_time(7)  # Valid for 1 week
        }
        return cls.create(**cls.merge_kwargs(temporary_defaults, kwargs))
    
    @classmethod
    def create_visitor(cls, **kwargs) -> Card:
        """Create a visitor card."""
        visitor_defaults = {
            'card_id': cls.generate_card_id('VISITOR'),
            'card_type': CardType.VISITOR,
            'valid_until': cls.future_time(1)  # Valid for 1 day
        }
        return cls.create(**cls.merge_kwargs(visitor_defaults, kwargs))
    
    @classmethod
    def create_inactive(cls, **kwargs) -> Card:
        """Create an inactive card."""
        inactive_defaults = {
            'status': CardStatus.INACTIVE,
            'card_id': cls.generate_card_id('INACTIVE')
        }
        return cls.create(**cls.merge_kwargs(inactive_defaults, kwargs))
    
    @classmethod
    def create_suspended(cls, **kwargs) -> Card:
        """Create a suspended card."""
        suspended_defaults = {
            'status': CardStatus.SUSPENDED,
            'card_id': cls.generate_card_id('SUSPENDED')
        }
        return cls.create(**cls.merge_kwargs(suspended_defaults, kwargs))
    
    @classmethod
    def create_lost(cls, **kwargs) -> Card:
        """Create a lost card."""
        lost_defaults = {
            'status': CardStatus.LOST,
            'card_id': cls.generate_card_id('LOST')
        }
        return cls.create(**cls.merge_kwargs(lost_defaults, kwargs))
    
    @classmethod
    def create_expired(cls, **kwargs) -> Card:
        """Create an expired card."""
        expired_defaults = {
            'card_id': cls.generate_card_id('EXPIRED'),
            'valid_until': cls.past_time(30)  # Expired 30 days ago
        }
        return cls.create(**cls.merge_kwargs(expired_defaults, kwargs))
    
    @classmethod
    def create_for_user(cls, user_id: UUID, **kwargs) -> Card:
        """Create a card for a specific user."""
        user_defaults = {'user_id': user_id}
        return cls.create(**cls.merge_kwargs(user_defaults, kwargs))


class CardModelFactory(DatabaseFactory):
    """Factory for creating CardModel database instances."""
    
    @classmethod
    def get_model_class(cls):
        return CardModel
    
    @classmethod
    def build(cls, **kwargs) -> Dict[str, Any]:
        """Build card model attributes with sensible defaults."""
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
        """Create a CardModel instance."""
        return cls.create_model(**kwargs)
    
    @classmethod
    def create_master(cls, **kwargs) -> CardModel:
        """Create a master card model."""
        master_defaults = {
            'card_id': cls.generate_card_id('MASTER'),
            'card_type': 'master',
            'valid_until': cls.future_time(3650)
        }
        return cls.create(**cls.merge_kwargs(master_defaults, kwargs))
    
    @classmethod
    def create_temporary(cls, **kwargs) -> CardModel:
        """Create a temporary card model."""
        temporary_defaults = {
            'card_id': cls.generate_card_id('TEMP'),
            'card_type': 'temporary',
            'valid_until': cls.future_time(7)
        }
        return cls.create(**cls.merge_kwargs(temporary_defaults, kwargs))
    
    @classmethod
    def create_inactive(cls, **kwargs) -> CardModel:
        """Create an inactive card model."""
        inactive_defaults = {
            'status': 'inactive',
            'card_id': cls.generate_card_id('INACTIVE')
        }
        return cls.create(**cls.merge_kwargs(inactive_defaults, kwargs))
    
    @classmethod
    def create_suspended(cls, **kwargs) -> CardModel:
        """Create a suspended card model."""
        suspended_defaults = {
            'status': 'suspended',
            'card_id': cls.generate_card_id('SUSPENDED')
        }
        return cls.create(**cls.merge_kwargs(suspended_defaults, kwargs))
    
    @classmethod
    def create_for_user(cls, user_id: UUID, **kwargs) -> CardModel:
        """Create a card model for a specific user."""
        user_defaults = {'user_id': user_id}
        return cls.create(**cls.merge_kwargs(user_defaults, kwargs))
    
    @classmethod
    def create_batch(cls, count: int, **kwargs) -> list[CardModel]:
        """Create multiple card models."""
        return [cls.create(**kwargs) for _ in range(count)]


# Convenience aliases for backward compatibility
create_test_card = CardFactory.create
create_master_card = CardFactory.create_master
create_test_card_model = CardModelFactory.create