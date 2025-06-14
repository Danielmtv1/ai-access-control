"""
Domain entities for IoT device communication.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timezone
from typing import Optional, Dict, Any
from enum import Enum
from uuid import UUID, uuid4


class DeviceCommandType(Enum):
    """Types of commands that can be sent to devices."""
    UNLOCK = "unlock"
    LOCK = "lock"
    STATUS = "status"
    REBOOT = "reboot"
    UPDATE_CONFIG = "update_config"


class DoorAction(Enum):
    """Actions that can be performed on doors."""
    UNLOCK = "unlock"
    DENY = "deny"
    REQUIRE_PIN = "require_pin"
    ALREADY_OPEN = "already_open"


@dataclass
class DeviceAccessRequest:
    """Access request from IoT device to server."""
    card_id: str
    door_id: UUID
    device_id: str
    timestamp: datetime
    message_id: str
    pin: Optional[str] = None
    location_data: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create(cls, card_id: str, door_id: UUID, device_id: str, pin: Optional[str] = None) -> 'DeviceAccessRequest':
        """Factory method to create a new device access request."""
        return cls(
            card_id=card_id,
            door_id=door_id,
            device_id=device_id,
            pin=pin,
            timestamp=datetime.now(timezone.utc),
            message_id=str(uuid4())
        )


@dataclass
class DeviceAccessResponse:
    """Access response from server to IoT device."""
    access_granted: bool
    door_action: DoorAction
    reason: str
    message_id: str
    timestamp: datetime
    duration: int = 0  # seconds to keep unlocked
    user_name: Optional[str] = None
    card_type: Optional[str] = None
    requires_pin: bool = False
    
    @classmethod
    def create_granted(cls, reason: str, duration: int = 5, user_name: Optional[str] = None, 
                      card_type: Optional[str] = None) -> 'DeviceAccessResponse':
        """Create a granted access response."""
        return cls(
            access_granted=True,
            door_action=DoorAction.UNLOCK,
            reason=reason,
            duration=duration,
            user_name=user_name,
            card_type=card_type,
            message_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc)
        )
    
    @classmethod
    def create_denied(cls, reason: str, requires_pin: bool = False) -> 'DeviceAccessResponse':
        """Create a denied access response."""
        return cls(
            access_granted=False,
            door_action=DoorAction.REQUIRE_PIN if requires_pin else DoorAction.DENY,
            reason=reason,
            requires_pin=requires_pin,
            message_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc)
        )


@dataclass
class DoorCommand:
    """Command to be sent to door device."""
    command: DeviceCommandType
    device_id: str
    message_id: str
    timestamp: datetime
    parameters: Dict[str, Any]
    timeout: int = field(default_factory=lambda: __import__('app.config', fromlist=['get_settings']).get_settings().MQTT_COMMAND_TIMEOUT)
    requires_ack: bool = True
    
    @classmethod
    def create_unlock(cls, device_id: str, duration: int = None) -> 'DoorCommand':
        """Create an unlock command."""
        if duration is None:
            from app.config import get_settings
            duration = get_settings().DEFAULT_UNLOCK_DURATION
        return cls(
            command=DeviceCommandType.UNLOCK,
            device_id=device_id,
            parameters={"duration": duration},
            message_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc)
        )
    
    @classmethod
    def create_lock(cls, device_id: str) -> 'DoorCommand':
        """Create a lock command."""
        return cls(
            command=DeviceCommandType.LOCK,
            device_id=device_id,
            parameters={},
            message_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc)
        )
    
    @classmethod
    def create_status_request(cls, device_id: str) -> 'DoorCommand':
        """Create a status request command."""
        return cls(
            command=DeviceCommandType.STATUS,
            device_id=device_id,
            parameters={},
            requires_ack=True,
            message_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc)
        )


@dataclass
class DeviceStatus:
    """Status information from IoT device."""
    device_id: str
    online: bool
    door_state: str  # "locked", "unlocked", "unknown", "error"
    battery_level: Optional[int] = None  # percentage
    signal_strength: Optional[int] = None  # dBm or percentage
    last_heartbeat: Optional[datetime] = None
    error_message: Optional[str] = None
    firmware_version: Optional[str] = None
    
    def is_healthy(self) -> bool:
        """Check if device is in healthy state."""
        if not self.online:
            return False
        
        if self.battery_level is not None and self.battery_level < 20:
            return False
        
        if self.error_message:
            return False
        
        return True


@dataclass
class DeviceEvent:
    """Event reported by IoT device."""
    device_id: str
    event_type: str
    timestamp: datetime
    message_id: str
    details: Dict[str, Any]
    severity: str = "info"  # "info", "warning", "error", "critical"
    
    @classmethod
    def create_door_opened(cls, device_id: str, card_id: Optional[str] = None) -> 'DeviceEvent':
        """Create door opened event."""
        return cls(
            device_id=device_id,
            event_type="door_opened",
            details={"card_id": card_id} if card_id else {},
            message_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc)
        )
    
    @classmethod
    def create_door_forced(cls, device_id: str) -> 'DeviceEvent':
        """Create door forced open event."""
        return cls(
            device_id=device_id,
            event_type="door_forced",
            details={},
            severity="critical",
            message_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc)
        )
    
    @classmethod
    def create_tamper_alert(cls, device_id: str, details: Dict[str, Any]) -> 'DeviceEvent':
        """Create tamper alert event."""
        return cls(
            device_id=device_id,
            event_type="tamper_alert",
            details=details,
            severity="critical",
            message_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc)
        )


@dataclass
class CommandAcknowledgment:
    """Acknowledgment of command execution from device."""
    message_id: str  # Original command message ID
    device_id: str
    status: str  # "success", "failed", "timeout", "invalid"
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None  # seconds
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
    
    def is_successful(self) -> bool:
        """Check if command was executed successfully."""
        return self.status == "success"