from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from enum import Enum

class UserStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive" 
    SUSPENDED = "suspended"

class Role(Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    USER = "user"
    VIEWER = "viewer"

@dataclass
class User:
    """Domain entity for User - Clean domain logic"""
    id: int
    email: str
    hashed_password: str
    full_name: str
    roles: List[Role]
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    def is_active(self) -> bool:
        """Business logic: User can authenticate"""
        return self.status == UserStatus.ACTIVE
    
    def has_role(self, role: Role) -> bool:
        """Business logic: Check if user has specific role"""
        return role in self.roles
    
    def has_any_role(self, roles: List[Role]) -> bool:
        """Business logic: Check if user has any of the roles"""
        return any(role in self.roles for role in roles)
    
    def can_access_admin_panel(self) -> bool:
        """Business logic: Admin access"""
        return self.is_active() and self.has_role(Role.ADMIN)
    
    def can_manage_devices(self) -> bool:
        """Business logic: Device management"""
        return self.is_active() and self.has_any_role([Role.ADMIN, Role.OPERATOR])
    
    def can_view_access_logs(self) -> bool:
        """Business logic: Access log viewing"""
        return self.is_active() and self.has_any_role([Role.ADMIN, Role.OPERATOR, Role.VIEWER]) 