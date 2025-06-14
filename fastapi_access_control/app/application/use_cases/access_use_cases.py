"""
Access validation use cases.
"""
from datetime import datetime, timezone, time
from typing import Optional
import logging
import json
from uuid import UUID
from app.api.schemas.access_schemas import AccessValidationResult
from app.ports.card_repository_port import CardRepositoryPort
from app.ports.door_repository_port import DoorRepositoryPort
from app.ports.permission_repository_port import PermissionRepositoryPort
from app.ports.user_repository_port import UserRepositoryPort
from app.domain.services.mqtt_message_service import MqttMessageService
from app.domain.services.device_communication_service import DeviceCommunicationService
from app.domain.entities.mqtt_message import MqttMessage
from app.domain.entities.device_message import DeviceAccessResponse, DoorAction
from app.domain.exceptions import (
    EntityNotFoundError,
    CardNotFoundError,
    DoorNotFoundError,
    UserNotFoundError,
    InvalidCardError,
    InvalidDoorError,
    AccessDeniedError
)

logger = logging.getLogger(__name__)


class AccessValidator:
    """Handles core access validation logic."""
    
    def __init__(self, card_repository: CardRepositoryPort, door_repository: DoorRepositoryPort, 
                 user_repository: UserRepositoryPort, permission_repository: PermissionRepositoryPort):
        self.card_repository = card_repository
        self.door_repository = door_repository
        self.user_repository = user_repository
        self.permission_repository = permission_repository
    
    async def validate_card(self, card_id: str):
        """Validate card exists and is active."""
        card = await self.card_repository.get_by_card_id(card_id)
        if not card:
            raise CardNotFoundError(card_id)
        
        if not card.is_active():
            raise InvalidCardError(f"Card {card_id} is inactive")
        
        return card
    
    async def validate_door(self, door_id: UUID):
        """Validate door exists and is accessible."""
        door = await self.door_repository.get_by_id(door_id)
        if not door:
            raise DoorNotFoundError(str(door_id))
        
        if not door.is_accessible():
            raise InvalidDoorError(f"Door {door.name} is not accessible")
        
        if door.is_locked_out():
            raise AccessDeniedError(f"Door {door.name} is temporarily locked due to failed attempts")
        
        return door
    
    async def validate_user(self, user_id: UUID, card_id: str):
        """Validate user exists and is active."""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id), f"User for card {card_id} not found")
        
        if not user.is_active():
            raise InvalidCardError(f"User {user.email} is inactive")
        
        return user
    
    async def check_permission(self, user_id: UUID, door_id: UUID, timestamp: datetime) -> bool:
        """Check if user has permission to access door."""
        return await self.permission_repository.check_access(
            user_id=user_id,
            door_id=door_id,
            current_time=timestamp.time(),
            current_day=timestamp.strftime('%a').lower()
        )
    
    def validate_pin(self, pin: str, user, door) -> bool:
        """Validate PIN code (simple implementation)."""
        # In a real system, this would check against a secure PIN database
        # For now, accept any 4-8 digit PIN as valid
        return pin.isdigit() and 4 <= len(pin) <= 8


class AccessLogger:
    """Handles access attempt logging."""
    
    def __init__(self, mqtt_service: MqttMessageService):
        self.mqtt_service = mqtt_service
    
    async def log_access_attempt(self, card_id: str, door_id: UUID, success: bool, reason: str):
        """Log access attempt via MQTT."""
        try:
            payload = {
                "card_id": str(card_id),
                "door_id": str(door_id),
                "result": "granted" if success else "denied",
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            message = MqttMessage(
                topic=f"access/door_{str(door_id)}/attempts",
                message=json.dumps(payload),
                timestamp=datetime.now(timezone.utc)
            )
            await self.mqtt_service.save_message(message)
        except Exception as e:
            logger.error(f"Failed to log access attempt: {str(e)}")


class DeviceResponseHandler:
    """Handles device communication responses."""
    
    def __init__(self, device_communication_service: Optional[DeviceCommunicationService]):
        self.device_communication_service = device_communication_service
    
    async def send_granted_response(self, device_id: str, user_name: str, card_type: str, reason: str):
        """Send access granted response to device."""
        if not device_id or not self.device_communication_service:
            return
        
        try:
            device_response = DeviceAccessResponse.create_granted(
                reason=reason,
                duration=5,
                user_name=user_name,
                card_type=card_type
            )
            await self.device_communication_service.publish_access_response(device_id, device_response)
            await self.device_communication_service.send_unlock_command(device_id, duration=5)
        except Exception as device_error:
            logger.error(f"Failed to communicate with device {device_id}: {device_error}")
    
    async def send_denied_response(self, device_id: str, reason: str, requires_pin: bool = False):
        """Send access denied response to device."""
        if not device_id or not self.device_communication_service:
            return
        
        try:
            device_response = DeviceAccessResponse.create_denied(
                reason=reason,
                requires_pin=requires_pin
            )
            await self.device_communication_service.publish_access_response(device_id, device_response)
        except Exception as device_error:
            logger.error(f"Failed to communicate with device {device_id}: {device_error}")


class AccessRecorder:
    """Handles recording successful access attempts."""
    
    def __init__(self, card_repository: CardRepositoryPort, door_repository: DoorRepositoryPort):
        self.card_repository = card_repository
        self.door_repository = door_repository
    
    async def record_successful_access(self, card, door, user):
        """Record successful access attempt."""
        # Update card usage
        card.record_usage()
        await self.card_repository.update(card)
        
        # Update door access
        door.record_successful_access(user.id)
        await self.door_repository.update(door)


class ValidateAccessUseCase:
    """Use case for validating access requests from IoT devices."""
    
    def __init__(
        self,
        card_repository: CardRepositoryPort,
        door_repository: DoorRepositoryPort,
        permission_repository: PermissionRepositoryPort,
        user_repository: UserRepositoryPort,
        mqtt_service: MqttMessageService,
        device_communication_service: Optional[DeviceCommunicationService] = None
    ):
        self.validator = AccessValidator(card_repository, door_repository, user_repository, permission_repository)
        self.logger = AccessLogger(mqtt_service)
        self.device_handler = DeviceResponseHandler(device_communication_service)
        self.recorder = AccessRecorder(card_repository, door_repository)
        self.permission_repository = permission_repository
    
    async def execute(
        self, 
        card_id: str, 
        door_id: UUID, 
        pin: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> AccessValidationResult:
        """
        Validate access request with comprehensive business logic.
        
        Args:
            card_id: Physical card identifier
            door_id: Door ID to access
            pin: Optional PIN code for high-security doors
            device_id: Optional device ID for device communication
            
        Returns:
            AccessValidationResult with access decision and details
        """
        timestamp = datetime.now(timezone.utc)
        logger.info(f"Access validation request: card={card_id}, door={door_id}")
        
        try:
            # Validate entities
            card = await self.validator.validate_card(card_id)
            door = await self.validator.validate_door(door_id)
            user = await self.validator.validate_user(card.user_id, card_id)
            
            # Handle master card access
            if card.is_master_card():
                return await self._handle_master_card_access(card, door, user, device_id)
            
            # Check permissions for regular cards
            if not await self.validator.check_permission(user.id, door_id, timestamp):
                await self.logger.log_access_attempt(card_id, door_id, False, "No permission")
                raise AccessDeniedError(f"User {user.full_name} does not have permission to access {door.name}")
            
            # Handle PIN requirements
            if door.requires_master_access() and not pin:
                return await self._handle_pin_required(card, door, user, device_id)
            
            # Validate PIN if provided
            if pin and not self.validator.validate_pin(pin, user, door):
                await self.logger.log_access_attempt(card_id, door_id, False, "Invalid PIN")
                raise AccessDeniedError("Invalid PIN provided")
            
            # Grant access
            return await self._grant_access(card, door, user, device_id)
            
        except Exception as e:
            logger.error(f"Error validating access: {str(e)}")
            await self.logger.log_access_attempt(card_id, door_id, False, str(e))
            await self.device_handler.send_denied_response(device_id, str(e))
            raise
    
    async def _handle_master_card_access(self, card, door, user, device_id: Optional[str]) -> AccessValidationResult:
        """Handle master card access logic."""
        logger.info(f"Master card access granted: {card.card_id} to {door.name}")
        
        await self.recorder.record_successful_access(card, door, user)
        await self.logger.log_access_attempt(
            card.card_id, door.id, True, f"Master card access granted for {user.full_name}"
        )
        
        await self.device_handler.send_granted_response(
            device_id, user.full_name, "master", f"Master card access granted for {user.full_name}"
        )
        
        return AccessValidationResult(
            access_granted=True,
            reason=f"Master card access granted for {user.full_name}",
            door_name=door.name,
            user_name=user.full_name,
            card_type="master",
            requires_pin=False,
            card_id=card.card_id,
            door_id=door.id,
            user_id=user.id
        )
    
    async def _handle_pin_required(self, card, door, user, device_id: Optional[str]) -> AccessValidationResult:
        """Handle PIN requirement for high-security doors."""
        await self.logger.log_access_attempt(card.card_id, door.id, False, "PIN required")
        await self.device_handler.send_denied_response(
            device_id, f"PIN required for high-security door {door.name}", requires_pin=True
        )
        
        return AccessValidationResult(
            access_granted=False,
            reason=f"PIN required for high-security door {door.name}",
            door_name=door.name,
            user_name=user.full_name,
            card_type=card.card_type.value,
            requires_pin=True,
            card_id=card.card_id,
            door_id=door.id,
            user_id=user.id
        )
    
    async def _grant_access(self, card, door, user, device_id: Optional[str]) -> AccessValidationResult:
        """Grant access and handle all related tasks."""
        # Record successful access
        await self.recorder.record_successful_access(card, door, user)
        await self.logger.log_access_attempt(
            card.card_id, door.id, True, f"Access granted for {user.full_name}"
        )
        
        # Get permission for additional information
        permission = await self.permission_repository.get_by_user_and_door(user.id, door.id)
        valid_until = None
        if permission and permission.valid_until:
            valid_until = permission.valid_until.strftime('%H:%M')
        
        # Send device response
        await self.device_handler.send_granted_response(
            device_id, user.full_name, card.card_type.value, f"Access granted for {user.full_name}"
        )
        
        logger.info(f"Access granted: {card.card_id} to {door.name} for {user.full_name}")
        
        return AccessValidationResult(
            access_granted=True,
            reason=f"Access granted for {user.full_name}",
            door_name=door.name,
            user_name=user.full_name,
            card_type=card.card_type.value,
            requires_pin=door.requires_master_access(),
            valid_until=valid_until,
            card_id=card.card_id,
            door_id=door.id,
            user_id=user.id
        )
    
