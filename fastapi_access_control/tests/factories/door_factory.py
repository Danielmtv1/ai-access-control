"""
Door factory for creating test door entities and database models.
"""
from typing import Dict, Any, Optional
from uuid import UUID

from app.domain.entities.door import Door, DoorStatus, AccessSchedule
from app.infrastructure.database.models.door import DoorModel
from .base_factory import EntityFactory, DatabaseFactory


class DoorFactory(EntityFactory):
    """Factory for creating Door domain entities."""
    
    @classmethod
    def get_entity_class(cls):
        return Door
    
    @classmethod
    def build(cls, **kwargs) -> Dict[str, Any]:
        """Build door attributes with sensible defaults."""
        defaults = {
            'id': cls.generate_uuid('door'),
            'name': cls._generate_door_name(),
            'location': cls._generate_location(),
            'description': 'Test door for automated testing',
            'security_level': 'MEDIUM',
            'status': DoorStatus.ACTIVE,
            'max_attempts': 3,
            'lockout_duration': 300,  # 5 minutes
            'is_emergency_exit': False,
            'requires_pin': False,
            'access_schedule': None,
            'failed_attempts': 0,
            'locked_until': None,
            'last_access': None,
            'created_at': cls.current_utc_time(),
            'updated_at': cls.current_utc_time()
        }
        return cls.merge_kwargs(defaults, kwargs)
    
    @classmethod
    def create(cls, **kwargs) -> Door:
        """Create a Door entity."""
        return cls.create_entity(**kwargs)
    
    @classmethod
    def create_high_security(cls, **kwargs) -> Door:
        """Create a high security door."""
        high_security_defaults = {
            'name': cls._generate_door_name('SecureVault'),
            'security_level': 'HIGH',
            'requires_pin': True,
            'max_attempts': 1,
            'lockout_duration': 900  # 15 minutes
        }
        return cls.create(**cls.merge_kwargs(high_security_defaults, kwargs))
    
    @classmethod
    def create_critical_security(cls, **kwargs) -> Door:
        """Create a critical security door."""
        critical_defaults = {
            'name': cls._generate_door_name('CriticalArea'),
            'security_level': 'CRITICAL',
            'requires_pin': True,
            'max_attempts': 1,
            'lockout_duration': 1800  # 30 minutes
        }
        return cls.create(**cls.merge_kwargs(critical_defaults, kwargs))
    
    @classmethod
    def create_low_security(cls, **kwargs) -> Door:
        """Create a low security door."""
        low_security_defaults = {
            'name': cls._generate_door_name('CommonArea'),
            'security_level': 'LOW',
            'requires_pin': False,
            'max_attempts': 5,
            'lockout_duration': 60  # 1 minute
        }
        return cls.create(**cls.merge_kwargs(low_security_defaults, kwargs))
    
    @classmethod
    def create_emergency_exit(cls, **kwargs) -> Door:
        """Create an emergency exit door."""
        emergency_defaults = {
            'name': cls._generate_door_name('EmergencyExit'),
            'is_emergency_exit': True,
            'security_level': 'LOW',
            'requires_pin': False
        }
        return cls.create(**cls.merge_kwargs(emergency_defaults, kwargs))
    
    @classmethod
    def create_inactive(cls, **kwargs) -> Door:
        """Create an inactive door."""
        inactive_defaults = {
            'status': DoorStatus.INACTIVE,
            'name': cls._generate_door_name('Inactive')
        }
        return cls.create(**cls.merge_kwargs(inactive_defaults, kwargs))
    
    @classmethod
    def create_maintenance(cls, **kwargs) -> Door:
        """Create a door in maintenance mode."""
        maintenance_defaults = {
            'status': DoorStatus.MAINTENANCE,
            'name': cls._generate_door_name('Maintenance')
        }
        return cls.create(**cls.merge_kwargs(maintenance_defaults, kwargs))
    
    @classmethod
    def create_emergency_locked(cls, **kwargs) -> Door:
        """Create a door in emergency locked state."""
        emergency_locked_defaults = {
            'status': DoorStatus.EMERGENCY_LOCKED,
            'name': cls._generate_door_name('EmergencyLocked')
        }
        return cls.create(**cls.merge_kwargs(emergency_locked_defaults, kwargs))
    
    @classmethod
    def create_with_schedule(cls, **kwargs) -> Door:
        """Create a door with access schedule."""
        schedule = AccessSchedule(
            days_of_week=['mon', 'tue', 'wed', 'thu', 'fri'],
            start_time='09:00',
            end_time='17:00'
        )
        schedule_defaults = {
            'name': cls._generate_door_name('Scheduled'),
            'access_schedule': schedule
        }
        return cls.create(**cls.merge_kwargs(schedule_defaults, kwargs))
    
    @classmethod
    def create_24_7_access(cls, **kwargs) -> Door:
        """Create a door with 24/7 access schedule."""
        schedule_24_7 = AccessSchedule(
            days_of_week=['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
            start_time='00:00',
            end_time='23:59'
        )
        always_open_defaults = {
            'name': cls._generate_door_name('24x7Access'),
            'access_schedule': schedule_24_7
        }
        return cls.create(**cls.merge_kwargs(always_open_defaults, kwargs))
    
    @classmethod
    def _generate_door_name(cls, prefix: str = "TestDoor") -> str:
        """Generate a unique door name."""
        import secrets
        import string
        random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        return f"{prefix}_{random_suffix}"
    
    @classmethod
    def _generate_location(cls) -> str:
        """Generate a test location."""
        locations = [
            "Building A - Floor 1",
            "Building A - Floor 2", 
            "Building B - Basement",
            "Building C - Rooftop",
            "Main Entrance",
            "Server Room",
            "Storage Area",
            "Conference Room"
        ]
        import secrets
        return secrets.choice(locations)


class DoorModelFactory(DatabaseFactory):
    """Factory for creating DoorModel database instances."""
    
    @classmethod
    def get_model_class(cls):
        return DoorModel
    
    @classmethod
    def build(cls, **kwargs) -> Dict[str, Any]:
        """Build door model attributes with sensible defaults."""
        defaults = {
            'id': cls.generate_uuid('door'),
            'name': cls._generate_door_name(),
            'location': cls._generate_location(),
            'description': 'Test door for automated testing',
            'security_level': 'MEDIUM',
            'status': 'active',
            'max_attempts': 3,
            'lockout_duration': 300,
            'is_emergency_exit': False,
            'requires_pin': False,
            'default_schedule_data': None,
            'failed_attempts': 0,
            'locked_until': None,
            'last_access': None,
            'created_at': cls.current_utc_time(),
            'updated_at': cls.current_utc_time()
        }
        return cls.merge_kwargs(defaults, kwargs)
    
    @classmethod
    def create(cls, **kwargs) -> DoorModel:
        """Create a DoorModel instance."""
        return cls.create_model(**kwargs)
    
    @classmethod
    def create_high_security(cls, **kwargs) -> DoorModel:
        """Create a high security door model."""
        high_security_defaults = {
            'name': cls._generate_door_name('SecureVault'),
            'security_level': 'HIGH',
            'requires_pin': True,
            'max_attempts': 1,
            'lockout_duration': 900
        }
        return cls.create(**cls.merge_kwargs(high_security_defaults, kwargs))
    
    @classmethod
    def create_with_schedule(cls, **kwargs) -> DoorModel:
        """Create a door model with access schedule."""
        schedule_data = {
            'days_of_week': ['mon', 'tue', 'wed', 'thu', 'fri'],
            'start_time': '09:00',
            'end_time': '17:00'
        }
        schedule_defaults = {
            'name': cls._generate_door_name('Scheduled'),
            'default_schedule_data': schedule_data
        }
        return cls.create(**cls.merge_kwargs(schedule_defaults, kwargs))
    
    @classmethod
    def create_maintenance(cls, **kwargs) -> DoorModel:
        """Create a door model in maintenance mode."""
        maintenance_defaults = {
            'status': 'maintenance',
            'name': cls._generate_door_name('Maintenance')
        }
        return cls.create(**cls.merge_kwargs(maintenance_defaults, kwargs))
    
    @classmethod
    def create_batch(cls, count: int, **kwargs) -> list[DoorModel]:
        """Create multiple door models."""
        return [cls.create(**kwargs) for _ in range(count)]
    
    @classmethod
    def _generate_door_name(cls, prefix: str = "TestDoor") -> str:
        """Generate a unique door name."""
        import secrets
        import string
        random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        return f"{prefix}_{random_suffix}"
    
    @classmethod
    def _generate_location(cls) -> str:
        """Generate a test location."""
        locations = [
            "Building A - Floor 1",
            "Building A - Floor 2", 
            "Building B - Basement",
            "Building C - Rooftop",
            "Main Entrance",
            "Server Room",
            "Storage Area",
            "Conference Room"
        ]
        import secrets
        return secrets.choice(locations)


# Convenience aliases for backward compatibility
create_test_door = DoorFactory.create
create_high_security_door = DoorFactory.create_high_security
create_test_door_model = DoorModelFactory.create