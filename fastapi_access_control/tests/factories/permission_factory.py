"""
Permission factory for creating test permission entities and database models.
"""
from typing import Dict, Any, Optional, List
from uuid import UUID

from app.domain.entities.permission import Permission, PermissionStatus
from app.domain.entities.door import AccessSchedule
from app.infrastructure.database.models.permission import PermissionModel
from .base_factory import EntityFactory, DatabaseFactory


class PermissionFactory(EntityFactory):
    """Factory for creating Permission domain entities."""
    
    @classmethod
    def get_entity_class(cls):
        return Permission
    
    @classmethod
    def build(cls, **kwargs) -> Dict[str, Any]:
        """Build permission attributes with sensible defaults."""
        defaults = {
            'id': cls.generate_uuid('permission'),
            'user_id': kwargs.get('user_id', cls.generate_uuid('user')),
            'door_id': kwargs.get('door_id', cls.generate_uuid('door')),
            'card_id': kwargs.get('card_id', None),  # Optional specific card
            'status': PermissionStatus.ACTIVE,
            'valid_from': cls.current_utc_time(),
            'valid_until': cls.future_time(365),  # Valid for 1 year
            'access_schedule': None,
            'last_used': None,
            'usage_count': 0,
            'created_at': cls.current_utc_time(),
            'updated_at': cls.current_utc_time()
        }
        return cls.merge_kwargs(defaults, kwargs)
    
    @classmethod
    def create(cls, **kwargs) -> Permission:
        """Create a Permission entity."""
        return cls.create_entity(**kwargs)
    
    @classmethod
    def create_for_user_and_door(cls, user_id: UUID, door_id: UUID, **kwargs) -> Permission:
        """Create a permission for a specific user and door."""
        specific_defaults = {
            'user_id': user_id,
            'door_id': door_id
        }
        return cls.create(**cls.merge_kwargs(specific_defaults, kwargs))
    
    @classmethod
    def create_for_card_and_door(cls, card_id: UUID, door_id: UUID, **kwargs) -> Permission:
        """Create a permission for a specific card and door."""
        card_defaults = {
            'card_id': card_id,
            'door_id': door_id,
            'user_id': kwargs.get('user_id', cls.generate_uuid('user'))
        }
        return cls.create(**cls.merge_kwargs(card_defaults, kwargs))
    
    @classmethod
    def create_temporary(cls, **kwargs) -> Permission:
        """Create a temporary permission (1 day)."""
        temporary_defaults = {
            'valid_until': cls.future_time(1)  # Valid for 1 day
        }
        return cls.create(**cls.merge_kwargs(temporary_defaults, kwargs))
    
    @classmethod
    def create_long_term(cls, **kwargs) -> Permission:
        """Create a long-term permission (5 years)."""
        long_term_defaults = {
            'valid_until': cls.future_time(365 * 5)  # Valid for 5 years
        }
        return cls.create(**cls.merge_kwargs(long_term_defaults, kwargs))
    
    @classmethod
    def create_inactive(cls, **kwargs) -> Permission:
        """Create an inactive permission."""
        inactive_defaults = {
            'status': PermissionStatus.INACTIVE
        }
        return cls.create(**cls.merge_kwargs(inactive_defaults, kwargs))
    
    @classmethod
    def create_suspended(cls, **kwargs) -> Permission:
        """Create a suspended permission."""
        suspended_defaults = {
            'status': PermissionStatus.SUSPENDED
        }
        return cls.create(**cls.merge_kwargs(suspended_defaults, kwargs))
    
    @classmethod
    def create_expired(cls, **kwargs) -> Permission:
        """Create an expired permission."""
        expired_defaults = {
            'valid_until': cls.past_time(30)  # Expired 30 days ago
        }
        return cls.create(**cls.merge_kwargs(expired_defaults, kwargs))
    
    @classmethod
    def create_with_business_hours(cls, **kwargs) -> Permission:
        """Create a permission with business hours schedule."""
        business_schedule = AccessSchedule(
            days_of_week=['mon', 'tue', 'wed', 'thu', 'fri'],
            start_time='09:00',
            end_time='17:00'
        )
        business_defaults = {
            'access_schedule': business_schedule
        }
        return cls.create(**cls.merge_kwargs(business_defaults, kwargs))
    
    @classmethod
    def create_with_24_7_access(cls, **kwargs) -> Permission:
        """Create a permission with 24/7 access schedule."""
        all_access_schedule = AccessSchedule(
            days_of_week=['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
            start_time='00:00',
            end_time='23:59'
        )
        all_access_defaults = {
            'access_schedule': all_access_schedule
        }
        return cls.create(**cls.merge_kwargs(all_access_defaults, kwargs))
    
    @classmethod
    def create_weekend_only(cls, **kwargs) -> Permission:
        """Create a permission for weekends only."""
        weekend_schedule = AccessSchedule(
            days_of_week=['sat', 'sun'],
            start_time='00:00',
            end_time='23:59'
        )
        weekend_defaults = {
            'access_schedule': weekend_schedule
        }
        return cls.create(**cls.merge_kwargs(weekend_defaults, kwargs))
    
    @classmethod
    def create_batch_for_user(cls, user_id: UUID, door_ids: List[UUID], **kwargs) -> List[Permission]:
        """Create multiple permissions for a user across multiple doors."""
        permissions = []
        for door_id in door_ids:
            permission = cls.create_for_user_and_door(user_id, door_id, **kwargs)
            permissions.append(permission)
        return permissions


class PermissionModelFactory(DatabaseFactory):
    """Factory for creating PermissionModel database instances."""
    
    @classmethod
    def get_model_class(cls):
        return PermissionModel
    
    @classmethod
    def build(cls, **kwargs) -> Dict[str, Any]:
        """Build permission model attributes with sensible defaults."""
        defaults = {
            'id': cls.generate_uuid('permission'),
            'user_id': kwargs.get('user_id', cls.generate_uuid('user')),
            'door_id': kwargs.get('door_id', cls.generate_uuid('door')),
            'card_id': kwargs.get('card_id', None),
            'status': 'active',
            'valid_from': cls.current_utc_time(),
            'valid_until': cls.future_time(365),
            'access_schedule_data': None,
            'last_used': None,
            'usage_count': 0,
            'created_at': cls.current_utc_time(),
            'updated_at': cls.current_utc_time()
        }
        return cls.merge_kwargs(defaults, kwargs)
    
    @classmethod
    def create(cls, **kwargs) -> PermissionModel:
        """Create a PermissionModel instance."""
        return cls.create_model(**kwargs)
    
    @classmethod
    def create_for_user_and_door(cls, user_id: UUID, door_id: UUID, **kwargs) -> PermissionModel:
        """Create a permission model for a specific user and door."""
        specific_defaults = {
            'user_id': user_id,
            'door_id': door_id
        }
        return cls.create(**cls.merge_kwargs(specific_defaults, kwargs))
    
    @classmethod
    def create_with_schedule(cls, **kwargs) -> PermissionModel:
        """Create a permission model with access schedule."""
        schedule_data = {
            'days_of_week': ['mon', 'tue', 'wed', 'thu', 'fri'],
            'start_time': '09:00',
            'end_time': '17:00'
        }
        schedule_defaults = {
            'access_schedule_data': schedule_data
        }
        return cls.create(**cls.merge_kwargs(schedule_defaults, kwargs))
    
    @classmethod
    def create_inactive(cls, **kwargs) -> PermissionModel:
        """Create an inactive permission model."""
        inactive_defaults = {
            'status': 'inactive'
        }
        return cls.create(**cls.merge_kwargs(inactive_defaults, kwargs))
    
    @classmethod
    def create_batch(cls, count: int, **kwargs) -> List[PermissionModel]:
        """Create multiple permission models."""
        return [cls.create(**kwargs) for _ in range(count)]
    
    @classmethod
    def create_batch_for_user(cls, user_id: UUID, door_ids: List[UUID], **kwargs) -> List[PermissionModel]:
        """Create multiple permission models for a user across multiple doors."""
        permissions = []
        for door_id in door_ids:
            permission = cls.create_for_user_and_door(user_id, door_id, **kwargs)
            permissions.append(permission)
        return permissions


# Convenience aliases for backward compatibility
create_test_permission = PermissionFactory.create
create_user_door_permission = PermissionFactory.create_for_user_and_door
create_test_permission_model = PermissionModelFactory.create