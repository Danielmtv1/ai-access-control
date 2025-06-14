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
        """
        Returns the Permission entity class.
        """
        return Permission
    
    @classmethod
    def build(cls, **kwargs) -> Dict[str, Any]:
        """
        Builds a dictionary of permission attributes with default values for testing.
        
        Merges sensible defaults such as generated UUIDs, active status, 1-year validity, and timestamps with any provided overrides.
        """
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
        """
        Creates a Permission entity with default or overridden attributes.
        
        Keyword arguments can be provided to override default values such as IDs, status, validity period, access schedule, and timestamps.
        
        Returns:
            A Permission entity instance.
        """
        return cls.create_entity(**kwargs)
    
    @classmethod
    def create_for_user_and_door(cls, user_id: UUID, door_id: UUID, **kwargs) -> Permission:
        """
        Creates a Permission entity for a specified user and door.
        
        Args:
            user_id: The UUID of the user to assign the permission to.
            door_id: The UUID of the door for which the permission is granted.
        
        Returns:
            A Permission entity configured for the given user and door.
        """
        specific_defaults = {
            'user_id': user_id,
            'door_id': door_id
        }
        return cls.create(**cls.merge_kwargs(specific_defaults, kwargs))
    
    @classmethod
    def create_for_card_and_door(cls, card_id: UUID, door_id: UUID, **kwargs) -> Permission:
        """
        Creates a Permission entity for a specific card and door.
        
        If a user ID is not provided, a new one is generated automatically.
        """
        card_defaults = {
            'card_id': card_id,
            'door_id': door_id,
            'user_id': kwargs.get('user_id', cls.generate_uuid('user'))
        }
        return cls.create(**cls.merge_kwargs(card_defaults, kwargs))
    
    @classmethod
    def create_temporary(cls, **kwargs) -> Permission:
        """
        Creates a permission that is valid for 1 day.
        
        Any additional attributes can be provided via keyword arguments to override defaults.
        
        Returns:
            A Permission entity with a 1-day validity period.
        """
        temporary_defaults = {
            'valid_until': cls.future_time(1)  # Valid for 1 day
        }
        return cls.create(**cls.merge_kwargs(temporary_defaults, kwargs))
    
    @classmethod
    def create_long_term(cls, **kwargs) -> Permission:
        """
        Creates a permission valid for 5 years.
        
        Returns:
            A Permission instance with the validity period set to 5 years from the current time.
        """
        long_term_defaults = {
            'valid_until': cls.future_time(365 * 5)  # Valid for 5 years
        }
        return cls.create(**cls.merge_kwargs(long_term_defaults, kwargs))
    
    @classmethod
    def create_inactive(cls, **kwargs) -> Permission:
        """
        Creates a permission with inactive status.
        
        Any additional attributes can be provided via keyword arguments to override defaults.
        """
        inactive_defaults = {
            'status': PermissionStatus.INACTIVE
        }
        return cls.create(**cls.merge_kwargs(inactive_defaults, kwargs))
    
    @classmethod
    def create_suspended(cls, **kwargs) -> Permission:
        """
        Creates a permission with status set to suspended.
        
        Returns:
            A Permission entity with suspended status.
        """
        suspended_defaults = {
            'status': PermissionStatus.SUSPENDED
        }
        return cls.create(**cls.merge_kwargs(suspended_defaults, kwargs))
    
    @classmethod
    def create_expired(cls, **kwargs) -> Permission:
        """
        Creates a permission that expired 30 days ago.
        
        Returns:
            A Permission instance with the validity period set to end 30 days in the past.
        """
        expired_defaults = {
            'valid_until': cls.past_time(30)  # Expired 30 days ago
        }
        return cls.create(**cls.merge_kwargs(expired_defaults, kwargs))
    
    @classmethod
    def create_with_business_hours(cls, **kwargs) -> Permission:
        """
        Creates a permission with access restricted to business hours on weekdays.
        
        The generated permission allows access Monday through Friday from 09:00 to 17:00. Additional attributes can be overridden via keyword arguments.
        
        Returns:
            A Permission instance with a business hours access schedule.
        """
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
        """
        Creates a permission granting access at all times, every day of the week.
        
        Returns:
            A Permission instance with an access schedule allowing 24/7 access.
        """
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
        """
        Creates a permission with access restricted to weekends.
        
        The generated permission allows access only on Saturdays and Sundays, from 00:00 to 23:59.
        """
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
        """
        Creates a list of permissions for a user, assigning each permission to a different door.
        
        Args:
            user_id: The UUID of the user for whom permissions are created.
            door_ids: A list of UUIDs representing the doors to assign permissions to.
        
        Returns:
            A list of Permission instances, one for each door ID.
        """
        permissions = []
        for door_id in door_ids:
            permission = cls.create_for_user_and_door(user_id, door_id, **kwargs)
            permissions.append(permission)
        return permissions


class PermissionModelFactory(DatabaseFactory):
    """Factory for creating PermissionModel database instances."""
    
    @classmethod
    def get_model_class(cls):
        """
        Returns the PermissionModel class associated with this factory.
        """
        return PermissionModel
    
    @classmethod
    def build(cls, **kwargs) -> Dict[str, Any]:
        """
        Builds a dictionary of permission model attributes with default values for testing.
        
        Merges sensible defaults such as generated UUIDs, active status, validity period, and timestamps with any provided keyword arguments.
        """
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
        """
        Creates a PermissionModel instance with default or overridden attributes.
        
        Additional keyword arguments can be provided to override default values for the PermissionModel fields.
        """
        return cls.create_model(**kwargs)
    
    @classmethod
    def create_for_user_and_door(cls, user_id: UUID, door_id: UUID, **kwargs) -> PermissionModel:
        """
        Creates a PermissionModel instance for a specified user and door.
        
        Args:
            user_id: The UUID of the user for whom the permission model is created.
            door_id: The UUID of the door to associate with the permission model.
        
        Returns:
            A PermissionModel instance with the specified user and door IDs.
        """
        specific_defaults = {
            'user_id': user_id,
            'door_id': door_id
        }
        return cls.create(**cls.merge_kwargs(specific_defaults, kwargs))
    
    @classmethod
    def create_with_schedule(cls, **kwargs) -> PermissionModel:
        """
        Creates a PermissionModel instance with an access schedule limited to weekdays from 09:00 to 17:00.
        
        Additional keyword arguments can be provided to override default attributes.
        """
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
        """
        Creates a PermissionModel instance with status set to 'inactive'.
        
        Additional attributes can be provided via keyword arguments to override defaults.
        
        Returns:
            PermissionModel: The created inactive permission model instance.
        """
        inactive_defaults = {
            'status': 'inactive'
        }
        return cls.create(**cls.merge_kwargs(inactive_defaults, kwargs))
    
    @classmethod
    def create_batch(cls, count: int, **kwargs) -> List[PermissionModel]:
        """
        Creates a list of permission model instances.
        
        Args:
            count: The number of permission models to create.
        
        Returns:
            A list containing the specified number of PermissionModel instances.
        """
        return [cls.create(**kwargs) for _ in range(count)]
    
    @classmethod
    def create_batch_for_user(cls, user_id: UUID, door_ids: List[UUID], **kwargs) -> List[PermissionModel]:
        """
        Creates multiple PermissionModel instances for a user, one for each specified door.
        
        Args:
            user_id: The UUID of the user for whom permissions are created.
            door_ids: A list of UUIDs representing the doors to associate with the user.
        
        Returns:
            A list of PermissionModel instances, each corresponding to a user-door pair.
        """
        permissions = []
        for door_id in door_ids:
            permission = cls.create_for_user_and_door(user_id, door_id, **kwargs)
            permissions.append(permission)
        return permissions


# Convenience aliases for backward compatibility
create_test_permission = PermissionFactory.create
create_user_door_permission = PermissionFactory.create_for_user_and_door
create_test_permission_model = PermissionModelFactory.create