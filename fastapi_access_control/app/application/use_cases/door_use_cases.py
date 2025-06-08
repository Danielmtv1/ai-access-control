from typing import Optional, List
from datetime import datetime, UTC, time
from ...domain.entities.door import Door, DoorType, SecurityLevel, DoorStatus, AccessSchedule
from ...ports.door_repository_port import DoorRepositoryPort
from ...domain.exceptions import DomainError
import logging

logger = logging.getLogger(__name__)

class DoorNotFoundError(DomainError):
    """Door not found error"""
    pass

class CreateDoorUseCase:
    """Use case for creating new doors"""
    
    def __init__(self, door_repository: DoorRepositoryPort):
        self.door_repository = door_repository
    
    async def execute(self, 
                     name: str,
                     location: str,
                     door_type: str,
                     security_level: str,
                     description: Optional[str] = None,
                     requires_pin: bool = False,
                     max_attempts: int = 3,
                     lockout_duration: int = 300,
                     default_schedule_data: Optional[dict] = None) -> Door:
        """Create new door"""
        
        # Check if door name already exists
        existing_door = await self.door_repository.get_by_name(name)
        if existing_door:
            raise DomainError(f"Door with name '{name}' already exists")
        
        # Parse default schedule if provided
        default_schedule = None
        if default_schedule_data:
            try:
                default_schedule = AccessSchedule(
                    days_of_week=default_schedule_data.get('days_of_week', []),
                    start_time=datetime.strptime(default_schedule_data.get('start_time', '00:00'), '%H:%M').time(),
                    end_time=datetime.strptime(default_schedule_data.get('end_time', '23:59'), '%H:%M').time()
                )
            except (ValueError, KeyError) as e:
                raise DomainError(f"Invalid schedule data: {e}")
        
        # Create door entity
        now = datetime.now(UTC).replace(tzinfo=None)
        door = Door(
            id=0,  # Will be set by database
            name=name,
            location=location,
            description=description,
            door_type=DoorType(door_type),
            security_level=SecurityLevel(security_level),
            status=DoorStatus.ACTIVE,
            default_schedule=default_schedule,
            requires_pin=requires_pin,
            max_attempts=max_attempts,
            lockout_duration=lockout_duration,
            created_at=now,
            updated_at=now,
            failed_attempts=0
        )
        
        logger.info(f"Creating new door '{name}' at location '{location}'")
        return await self.door_repository.create(door)

class GetDoorUseCase:
    """Use case for getting door by ID"""
    
    def __init__(self, door_repository: DoorRepositoryPort):
        self.door_repository = door_repository
    
    async def execute(self, door_id: int) -> Door:
        """Get door by ID"""
        door = await self.door_repository.get_by_id(door_id)
        if not door:
            raise DoorNotFoundError(f"Door with ID {door_id} not found")
        return door

class GetDoorByNameUseCase:
    """Use case for getting door by name"""
    
    def __init__(self, door_repository: DoorRepositoryPort):
        self.door_repository = door_repository
    
    async def execute(self, name: str) -> Door:
        """Get door by name"""
        door = await self.door_repository.get_by_name(name)
        if not door:
            raise DoorNotFoundError(f"Door with name '{name}' not found")
        return door

class GetDoorsByLocationUseCase:
    """Use case for getting doors by location"""
    
    def __init__(self, door_repository: DoorRepositoryPort):
        self.door_repository = door_repository
    
    async def execute(self, location: str) -> List[Door]:
        """Get doors by location"""
        return await self.door_repository.get_by_location(location)

class UpdateDoorUseCase:
    """Use case for updating door"""
    
    def __init__(self, door_repository: DoorRepositoryPort):
        self.door_repository = door_repository
    
    async def execute(self, 
                     door_id: int,
                     name: Optional[str] = None,
                     location: Optional[str] = None,
                     description: Optional[str] = None,
                     door_type: Optional[str] = None,
                     security_level: Optional[str] = None,
                     requires_pin: Optional[bool] = None,
                     max_attempts: Optional[int] = None,
                     lockout_duration: Optional[int] = None,
                     default_schedule_data: Optional[dict] = None) -> Door:
        """Update door"""
        
        # Get existing door
        door = await self.door_repository.get_by_id(door_id)
        if not door:
            raise DoorNotFoundError(f"Door with ID {door_id} not found")
        
        # Update fields if provided
        if name and name != door.name:
            # Check if new name already exists
            existing_door = await self.door_repository.get_by_name(name)
            if existing_door and existing_door.id != door_id:
                raise DomainError(f"Door with name '{name}' already exists")
            door.name = name
        
        if location:
            door.location = location
        if description is not None:  # Allow empty string
            door.description = description
        if door_type:
            door.door_type = DoorType(door_type)
        if security_level:
            door.security_level = SecurityLevel(security_level)
        if requires_pin is not None:
            door.requires_pin = requires_pin
        if max_attempts:
            door.max_attempts = max_attempts
        if lockout_duration:
            door.lockout_duration = lockout_duration
        
        # Update default schedule if provided
        if default_schedule_data is not None:
            if default_schedule_data:  # Not empty dict
                try:
                    door.default_schedule = AccessSchedule(
                        days_of_week=default_schedule_data.get('days_of_week', []),
                        start_time=datetime.strptime(default_schedule_data.get('start_time', '00:00'), '%H:%M').time(),
                        end_time=datetime.strptime(default_schedule_data.get('end_time', '23:59'), '%H:%M').time()
                    )
                except (ValueError, KeyError) as e:
                    raise DomainError(f"Invalid schedule data: {e}")
            else:  # Empty dict means remove schedule
                door.default_schedule = None
        
        door.updated_at = datetime.now(UTC).replace(tzinfo=None)
        
        logger.info(f"Updating door {door_id}")
        return await self.door_repository.update(door)

class SetDoorStatusUseCase:
    """Use case for changing door status"""
    
    def __init__(self, door_repository: DoorRepositoryPort):
        self.door_repository = door_repository
    
    async def execute(self, door_id: int, status: str) -> Door:
        """Set door status"""
        
        # Get existing door
        door = await self.door_repository.get_by_id(door_id)
        if not door:
            raise DoorNotFoundError(f"Door with ID {door_id} not found")
        
        # Update status using domain logic
        if status == DoorStatus.ACTIVE.value:
            door.activate()
        elif status == DoorStatus.MAINTENANCE.value:
            door.set_maintenance_mode()
        elif status == DoorStatus.EMERGENCY_OPEN.value:
            door.set_emergency_open()
        elif status == DoorStatus.EMERGENCY_LOCKED.value:
            door.set_emergency_locked()
        else:
            door.status = DoorStatus(status)
            door.updated_at = datetime.now(UTC).replace(tzinfo=None)
        
        logger.info(f"Setting door {door_id} status to {status}")
        return await self.door_repository.update(door)

class ListDoorsUseCase:
    """Use case for listing doors with pagination"""
    
    def __init__(self, door_repository: DoorRepositoryPort):
        self.door_repository = door_repository
    
    async def execute(self, skip: int = 0, limit: int = 100) -> List[Door]:
        """List doors with pagination"""
        return await self.door_repository.list_doors(skip, limit)

class GetActiveDoorsUseCase:
    """Use case for getting active doors"""
    
    def __init__(self, door_repository: DoorRepositoryPort):
        self.door_repository = door_repository
    
    async def execute(self) -> List[Door]:
        """Get all active doors"""
        return await self.door_repository.get_active_doors()

class GetDoorsBySecurityLevelUseCase:
    """Use case for getting doors by security level"""
    
    def __init__(self, door_repository: DoorRepositoryPort):
        self.door_repository = door_repository
    
    async def execute(self, security_level: str) -> List[Door]:
        """Get doors by security level"""
        return await self.door_repository.get_doors_by_security_level(security_level)

class DeleteDoorUseCase:
    """Use case for deleting door"""
    
    def __init__(self, door_repository: DoorRepositoryPort):
        self.door_repository = door_repository
    
    async def execute(self, door_id: int) -> bool:
        """Delete door"""
        
        # Check if door exists
        door = await self.door_repository.get_by_id(door_id)
        if not door:
            raise DoorNotFoundError(f"Door with ID {door_id} not found")
        
        logger.info(f"Deleting door {door_id}")
        return await self.door_repository.delete(door_id)