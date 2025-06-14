from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timezone, time
from enum import Enum
from uuid import UUID
class PermissionStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    EXPIRED = "expired"

@dataclass
class Permission:
    """Domain entity for Permission - Links users/cards to doors with schedules"""
    id: UUID
    user_id: UUID
    door_id: UUID
    status: PermissionStatus
    valid_from: datetime
    created_by: UUID  # User who created this permission
    created_at: datetime
    updated_at: datetime
    card_id: Optional[UUID] = None  # Optional: permission can be user-based or card-based
    valid_until: Optional[datetime] = None
    access_schedule: Optional[str] = None  # JSON string with schedule data
    pin_required: bool = False
    last_used: Optional[datetime] = None
    
    def is_active(self) -> bool:
        """Business logic: Permission is currently valid"""
        if self.status != PermissionStatus.ACTIVE:
            return False
            
        now = datetime.now()
        if now < self.valid_from:
            return False
            
        if self.valid_until and now > self.valid_until:
            return False
            
        return True
    
    def is_expired(self) -> bool:
        """
        Determines whether the permission has expired.
        
        Returns:
            True if the current time is after the permission's valid_until timestamp; False if no expiration is set or the permission is still valid.
        """
        if not self.valid_until:
            return False
        return datetime.now() > self.valid_until
    
    def can_access_door(self, door_id: UUID) -> bool:
        """
        Determines if the permission grants access to the specified door.
        
        Args:
            door_id: The UUID of the door to check access for.
        
        Returns:
            True if the permission is active and associated with the given door ID; otherwise, False.
        """
        return self.is_active() and self.door_id == door_id
    
    def can_access_with_card(self, card_id: UUID) -> bool:
        """
        Determines if access is permitted with the specified card.
        
        Returns True if the permission is active and either not restricted to a specific card or the provided card ID matches the assigned card.
        """
        if not self.is_active():
            return False
            
        # If permission is not tied to a specific card, any user card can be used
        if self.card_id is None:
            return True
            
        return self.card_id == card_id
    
    def record_usage(self) -> None:
        """Business logic: Record permission usage"""
        self.last_used = datetime.now()
        self.updated_at = datetime.now()
    
    def suspend(self) -> None:
        """Business logic: Suspend permission"""
        self.status = PermissionStatus.SUSPENDED
        self.updated_at = datetime.now()
    
    def activate(self) -> None:
        """Business logic: Activate permission"""
        self.status = PermissionStatus.ACTIVE
        self.updated_at = datetime.now()
    
    def extend_validity(self, new_valid_until: datetime) -> None:
        """Business logic: Extend permission validity"""
        self.valid_until = new_valid_until
        self.updated_at = datetime.now()