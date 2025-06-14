from abc import ABC, abstractmethod
from typing import Optional, List
from ..domain.entities.door import Door
from uuid import UUID
class DoorRepositoryPort(ABC):
    """Port for Door repository operations"""
    
    @abstractmethod
    async def create(self, door: Door) -> Door:
        """Create a new door"""
        pass
    
    @abstractmethod
    async def get_by_id(self, door_id: UUID) -> Optional[Door]:
        """Get door by ID"""
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
        """Update existing door"""
        pass
    
    @abstractmethod
    async def delete(self, door_id: UUID) -> bool:
        """Delete door by ID"""
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