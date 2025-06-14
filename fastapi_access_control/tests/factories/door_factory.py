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
        """
        Returns the Door entity class.
        """
        return Door
    
    @classmethod
    def build(cls, **kwargs) -> Dict[str, Any]:
        """
        Constructs a dictionary of door attributes with default values for testing.
        
        Any provided keyword arguments override the corresponding defaults.
        """
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
        """
        Creates a Door domain entity with default attributes, allowing overrides via keyword arguments.
        
        Args:
        	**kwargs: Attribute values to override the defaults.
        
        Returns:
        	A Door entity instance with the specified or default attributes.
        """
        return cls.create_entity(**kwargs)
    
    @classmethod
    def create_high_security(cls, **kwargs) -> Door:
        """
        Creates a Door entity configured as a high security door.
        
        The door will have a unique name prefixed with "SecureVault", security level set to HIGH, require a PIN, allow only one attempt, and have a 15-minute lockout duration. Additional attributes can be overridden via keyword arguments.
        
        Returns:
            A Door entity with high security settings.
        """
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
        """
        Creates a Door entity configured as a critical security door.
        
        The door will have a unique name prefixed with "CriticalArea", security level set to CRITICAL, require a PIN, allow only one access attempt, and enforce a 30-minute lockout on failure. Additional attributes can be overridden via keyword arguments.
        
        Returns:
            A Door entity with critical security settings.
        """
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
        """
        Creates a low security Door entity with default attributes.
        
        The door will have a name prefixed with "CommonArea", security level set to LOW, no PIN required, a maximum of 5 attempts, and a 1-minute lockout duration. Additional attributes can be overridden via keyword arguments.
        
        Returns:
            A Door entity instance with low security settings.
        """
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
        """
        Creates a Door entity configured as an emergency exit.
        
        The returned door has a unique name prefixed with "EmergencyExit", is marked as an emergency exit, set to low security, and does not require a PIN. Additional attributes can be overridden via keyword arguments.
        
        Returns:
            A Door entity representing an emergency exit.
        """
        emergency_defaults = {
            'name': cls._generate_door_name('EmergencyExit'),
            'is_emergency_exit': True,
            'security_level': 'LOW',
            'requires_pin': False
        }
        return cls.create(**cls.merge_kwargs(emergency_defaults, kwargs))
    
    @classmethod
    def create_inactive(cls, **kwargs) -> Door:
        """
        Creates a Door entity with inactive status.
        
        Any provided keyword arguments override the default inactive attributes.
        """
        inactive_defaults = {
            'status': DoorStatus.INACTIVE,
            'name': cls._generate_door_name('Inactive')
        }
        return cls.create(**cls.merge_kwargs(inactive_defaults, kwargs))
    
    @classmethod
    def create_maintenance(cls, **kwargs) -> Door:
        """
        Creates a Door entity with maintenance status.
        
        Additional attributes can be provided to override the defaults.
        """
        maintenance_defaults = {
            'status': DoorStatus.MAINTENANCE,
            'name': cls._generate_door_name('Maintenance')
        }
        return cls.create(**cls.merge_kwargs(maintenance_defaults, kwargs))
    
    @classmethod
    def create_emergency_locked(cls, **kwargs) -> Door:
        """
        Creates a Door entity with status set to emergency locked.
        
        Additional attributes can be provided to override the defaults.
        """
        emergency_locked_defaults = {
            'status': DoorStatus.EMERGENCY_LOCKED,
            'name': cls._generate_door_name('EmergencyLocked')
        }
        return cls.create(**cls.merge_kwargs(emergency_locked_defaults, kwargs))
    
    @classmethod
    def create_with_schedule(cls, **kwargs) -> Door:
        """
        Creates a Door entity with an access schedule set to weekdays from 09:00 to 17:00.
        
        Additional attributes can be provided to override the defaults.
        """
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
        """
        Creates a door entity configured with a 24/7 access schedule.
        
        The returned door allows access every day of the week, from 00:00 to 23:59. Additional attributes can be customized via keyword arguments.
        
        Returns:
            A Door entity with unrestricted daily access.
        """
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
        """
        Generates a unique door name by appending a random 4-character alphanumeric suffix to the given prefix.
        
        Args:
            prefix: The prefix to use for the door name. Defaults to "TestDoor".
        
        Returns:
            A unique door name string in the format "{prefix}_{suffix}".
        """
        import secrets
        import string
        random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        return f"{prefix}_{random_suffix}"
    
    @classmethod
    def _generate_location(cls) -> str:
        """
        Selects and returns a random location string from a predefined list of test locations.
        """
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
        """
        Returns the DoorModel class associated with this factory.
        """
        return DoorModel
    
    @classmethod
    def build(cls, **kwargs) -> Dict[str, Any]:
        """
        Builds a dictionary of door model attributes with default values for testing.
        
        Any provided keyword arguments override the corresponding defaults.
        """
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
        """
        Creates a DoorModel database instance with default attributes, allowing overrides.
        
        Returns:
            A DoorModel instance with attributes merged from defaults and any provided keyword arguments.
        """
        return cls.create_model(**kwargs)
    
    @classmethod
    def create_high_security(cls, **kwargs) -> DoorModel:
        """
        Creates a DoorModel instance representing a high security door.
        
        Merges high security defaults—including a unique name with the "SecureVault" prefix, security level set to "HIGH", PIN requirement enabled, a single allowed attempt, and a 15-minute lockout duration—with any provided overrides.
        """
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
        """
        Creates a DoorModel instance with a default access schedule for weekdays from 9:00 to 17:00.
        
        Additional attributes can be provided to override the defaults.
        """
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
        """
        Creates a DoorModel instance with status set to maintenance.
        
        Additional attributes can be provided to override the default maintenance settings.
        """
        maintenance_defaults = {
            'status': 'maintenance',
            'name': cls._generate_door_name('Maintenance')
        }
        return cls.create(**cls.merge_kwargs(maintenance_defaults, kwargs))
    
    @classmethod
    def create_batch(cls, count: int, **kwargs) -> list[DoorModel]:
        """
        Creates a list of DoorModel instances with optional attribute overrides.
        
        Args:
            count: The number of DoorModel instances to create.
        
        Returns:
            A list containing the specified number of DoorModel instances.
        """
        return [cls.create(**kwargs) for _ in range(count)]
    
    @classmethod
    def _generate_door_name(cls, prefix: str = "TestDoor") -> str:
        """
        Generates a unique door name by appending a random 4-character alphanumeric suffix to the given prefix.
        
        Args:
            prefix: The prefix to use for the door name. Defaults to "TestDoor".
        
        Returns:
            A unique door name string in the format "{prefix}_{suffix}".
        """
        import secrets
        import string
        random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        return f"{prefix}_{random_suffix}"
    
    @classmethod
    def _generate_location(cls) -> str:
        """
        Selects and returns a random location string from a predefined list of test locations.
        """
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