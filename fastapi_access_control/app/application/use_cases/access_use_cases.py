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
        """
                 Initializes the AccessValidator with repositories for cards, doors, users, and permissions.
                 """
                 self.card_repository = card_repository
        self.door_repository = door_repository
        self.user_repository = user_repository
        self.permission_repository = permission_repository
    
    async def validate_card(self, card_id: str):
        """
        Asynchronously validates that a card exists and is active.
        
        Raises:
            CardNotFoundError: If the card does not exist.
            InvalidCardError: If the card is inactive.
        
        Returns:
            The card object if validation succeeds.
        """
        card = await self.card_repository.get_by_card_id(card_id)
        if not card:
            raise CardNotFoundError(card_id)
        
        if not card.is_active():
            raise InvalidCardError(f"Card {card_id} is inactive")
        
        return card
    
    async def validate_door(self, door_id: UUID):
        """
        Validates that a door exists, is accessible, and is not locked out.
        
        Raises:
            DoorNotFoundError: If the door does not exist.
            InvalidDoorError: If the door is not accessible.
            AccessDeniedError: If the door is temporarily locked out.
        
        Returns:
            The validated door object.
        """
        door = await self.door_repository.get_by_id(door_id)
        if not door:
            raise DoorNotFoundError(str(door_id))
        
        if not door.is_accessible():
            raise InvalidDoorError(f"Door {door.name} is not accessible")
        
        if door.is_locked_out():
            raise AccessDeniedError(f"Door {door.name} is temporarily locked due to failed attempts")
        
        return door
    
    async def validate_user(self, user_id: UUID, card_id: str):
        """
        Validates that a user exists and is active for the given user and card IDs.
        
        Raises:
            UserNotFoundError: If the user does not exist.
            InvalidCardError: If the user is inactive.
        
        Returns:
            The user object if validation succeeds.
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id), f"User for card {card_id} not found")
        
        if not user.is_active():
            raise InvalidCardError(f"User {user.email} is inactive")
        
        return user
    
    async def check_permission(self, user_id: UUID, door_id: UUID, timestamp: datetime) -> bool:
        """
        Checks whether the specified user has permission to access the given door at the provided date and time.
        
        Args:
            user_id: The unique identifier of the user.
            door_id: The unique identifier of the door.
            timestamp: The date and time of the access attempt.
        
        Returns:
            True if the user has permission to access the door at the specified time; otherwise, False.
        """
        return await self.permission_repository.check_access(
            user_id=user_id,
            door_id=door_id,
            current_time=timestamp.time(),
            current_day=timestamp.strftime('%a').lower()
        )
    
    def validate_pin(self, pin: str, user, door) -> bool:
        """
        Validates whether the provided PIN is a numeric code between 4 and 8 digits.
        
        Args:
            pin: The PIN code to validate.
            user: The user attempting access (not used in this implementation).
            door: The door being accessed (not used in this implementation).
        
        Returns:
            True if the PIN is numeric and 4 to 8 digits long, otherwise False.
        """
        # In a real system, this would check against a secure PIN database
        # For now, accept any 4-8 digit PIN as valid
        return pin.isdigit() and 4 <= len(pin) <= 8


class AccessLogger:
    """Handles access attempt logging."""
    
    def __init__(self, mqtt_service: MqttMessageService):
        """
        Initializes the AccessLogger with the provided MQTT message service.
        """
        self.mqtt_service = mqtt_service
    
    async def log_access_attempt(self, card_id: str, door_id: UUID, success: bool, reason: str):
        """
        Asynchronously logs an access attempt to a door via MQTT.
        
        Records the card ID, door ID, result (granted or denied), reason, and timestamp by sending a message to the appropriate MQTT topic.
        """
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
        """
        Initializes the DeviceResponseHandler with an optional device communication service.
        
        Args:
            device_communication_service: Service used to communicate with access control devices. If not provided, device responses will not be sent.
        """
        self.device_communication_service = device_communication_service
    
    async def send_granted_response(self, device_id: str, user_name: str, card_type: str, reason: str):
        """
        Sends an access granted response and unlock command to the specified device.
        
        If device communication is unavailable or the device ID is missing, the operation is skipped. Errors during communication are logged but do not interrupt execution.
        """
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
        """
        Sends an access denied response to the specified device.
        
        If a device communication service is available, constructs and publishes a denial response, optionally indicating that a PIN is required.
        """
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
        """
        Initializes the AccessRecorder with repositories for cards and doors.
        """
        self.card_repository = card_repository
        self.door_repository = door_repository
    
    async def record_successful_access(self, card, door, user):
        """
        Records a successful access event by updating card usage and door access records.
        
        This method updates the card's usage statistics and the door's access log to reflect a successful access attempt by the specified user.
        """
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
        """
        Initializes the ValidateAccessUseCase with repositories and services for access validation, logging, device communication, and access recording.
        """
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
        Validates an access request by orchestrating card, door, and user validation, permission checks, and PIN enforcement.
        
        Performs comprehensive business logic for access control, including master card handling, permission verification, PIN requirements for high-security doors, and device communication. Logs all access attempts and communicates results to devices. Returns an `AccessValidationResult` indicating the outcome and relevant details.
        
        Args:
            card_id: The identifier of the physical access card.
            door_id: The UUID of the door being accessed.
            pin: Optional PIN code required for certain doors.
            device_id: Optional device identifier for device communication.
        
        Returns:
            An `AccessValidationResult` containing the access decision, reason, and metadata.
        
        Raises:
            AccessDeniedError or other exceptions if validation fails or access is denied.
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
        """
        Grants access using a master card, records the event, logs the attempt, and notifies the device.
        
        This method is invoked when a master card is used for access. It records the successful access, logs the attempt as granted, sends a granted response to the device, and returns an access validation result indicating success.
        """
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
        """
        Handles access denial when a PIN is required for a high-security door.
        
        Logs the denied access attempt, notifies the device that a PIN is required, and returns an access validation result indicating that a PIN is needed for entry.
        """
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
        """
        Grants access to a user and performs all related actions, including recording the event, logging, device notification, and result construction.
        
        Args:
            card: The card entity used for access.
            door: The door entity being accessed.
            user: The user entity requesting access.
            device_id: Optional device identifier for sending responses.
        
        Returns:
            An AccessValidationResult indicating access was granted, with relevant metadata.
        """
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
    
