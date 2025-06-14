from abc import ABC, abstractmethod
from typing import Optional, List
from ..domain.entities.door import Door
from uuid import UUID
class DoorRepositoryPort(ABC):
    """Port for Door repository operations"""
    
    @abstractmethod
    async def create(self, door: Door) -> Door:
        """
        Creates a new door entity asynchronously.
        
        Args:
        	door: The Door object to be created.
        
        Returns:
        	The created Door instance.
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, door_id: UUID) -> Optional[Door]:
        """
        Retrieves a door entity by its unique identifier.
        
        Args:
            door_id: The UUID of the door to retrieve.
        
        Returns:
            The Door object if found, or None if no door with the given ID exists.
        """
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Door]:
        """Get door by name"""
        pass
    
    @abstractmethod
    async def get_by_location(self, location: str) -> List[Door]:
        """Get doors by location"""
        pass
    
    @abstractmethod
    async def update(self, door: Door) -> Door:
        """
        Updates an existing door entity and returns the updated door.
        
        Args:
            door: The door entity with updated information.
        
        Returns:
            The updated door entity.
        """
        pass
    
    @abstractmethod
    async def delete(self, door_id: UUID) -> bool:
        """
        Deletes a door entity by its unique identifier.
        
        Args:
            door_id: The UUID of the door to delete.
        
        Returns:
            True if the door was successfully deleted, False otherwise.
        """
        pass
    
    @abstractmethod
    async def list_doors(self, skip: int = 0, limit: int = 100) -> List[Door]:
        """List doors with pagination"""
        pass
    
    @abstractmethod
    async def get_active_doors(self) -> List[Door]:
        """Get all active doors"""
        pass
    
    @abstractmethod
    async def get_doors_by_security_level(self, security_level: str) -> List[Door]:
        """Get doors by security level"""
        pass