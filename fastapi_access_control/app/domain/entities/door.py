from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timezone, time, timedelta
from enum import Enum
from uuid import UUID

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DoorStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    EMERGENCY_OPEN = "emergency_open"
    EMERGENCY_LOCKED = "emergency_locked"

class DoorType(Enum):
    ENTRANCE = "entrance"
    EXIT = "exit"
    BIDIRECTIONAL = "bidirectional"
    EMERGENCY = "emergency"

@dataclass
class AccessSchedule:
    """Value object for access schedule"""
    days_of_week: List[int]  # 0=Monday, 6=Sunday
    start_time: time
    end_time: time
    
    def is_access_allowed_now(self) -> bool:
        """Check if access is allowed at current time"""
        now = datetime.now()
        current_day = now.weekday()
        current_time = now.time()
        
        if current_day not in self.days_of_week:
            return False
            
        return self.start_time <= current_time <= self.end_time

@dataclass
class Door:
    """Domain entity for Door - Clean domain logic"""
    id: UUID
    name: str
    location: str
    door_type: DoorType
    security_level: SecurityLevel
    status: DoorStatus
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
    default_schedule: Optional[AccessSchedule] = None
    requires_pin: bool = False
    max_attempts: int = 3
    lockout_duration: int = 300  # seconds
    last_access: Optional[datetime] = None
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    def is_active(self) -> bool:
        """Business logic: Door is operational"""
        return self.status == DoorStatus.ACTIVE
    
    def is_accessible(self) -> bool:
        """Business logic: Door can be accessed"""
        if not self.is_active():
            return False
            
        if self.is_locked_out():
            return False
            
        if self.default_schedule:
            return self.default_schedule.is_access_allowed_now()
            
        return True
    
    def is_locked_out(self) -> bool:
        """Business logic: Door is temporarily locked due to failed attempts"""
        if not self.locked_until:
            return False
        return datetime.now() < self.locked_until
    
    def is_high_security(self) -> bool:
        """Business logic: High security door requires special permissions"""
        return self.security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]
    
    def requires_master_access(self) -> bool:
        """Business logic: Critical security level requires master card"""
        return self.security_level == SecurityLevel.CRITICAL
    
    def record_successful_access(self, user_id: UUID) -> None:
        """Business logic: Record successful access"""
        self.last_access = datetime.now()
        self.failed_attempts = 0
        self.locked_until = None
        self.updated_at = datetime.now()
    
    def record_failed_attempt(self) -> None:
        """Business logic: Record failed access attempt"""
        self.failed_attempts += 1
        
        if self.failed_attempts >= self.max_attempts:
            self.locked_until = datetime.now() + timedelta(seconds=self.lockout_duration)
            
        self.updated_at = datetime.now()
    
    def reset_failed_attempts(self) -> None:
        """Business logic: Reset failed attempts counter"""
        self.failed_attempts = 0
        self.locked_until = None
        self.updated_at = datetime.now()
    
    def set_emergency_open(self) -> None:
        """Business logic: Emergency mode - door stays open"""
        self.status = DoorStatus.EMERGENCY_OPEN
        self.updated_at = datetime.now()
    
    def set_emergency_locked(self) -> None:
        """Business logic: Emergency mode - door stays locked"""
        self.status = DoorStatus.EMERGENCY_LOCKED
        self.updated_at = datetime.now()
    
    def set_maintenance_mode(self) -> None:
        """Business logic: Maintenance mode"""
        self.status = DoorStatus.MAINTENANCE
        self.updated_at = datetime.now()
    
    def activate(self) -> None:
        """Business logic: Activate door"""
        self.status = DoorStatus.ACTIVE
        self.reset_failed_attempts()
        self.updated_at = datetime.now()

