"""
Access validation use cases.
"""
from datetime import datetime, timezone, time
from typing import Optional
import logging
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
    InvalidCardError,
    InvalidDoorError,
    AccessDeniedError
)

logger = logging.getLogger(__name__)


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
        self.card_repository = card_repository
        self.door_repository = door_repository
        self.permission_repository = permission_repository
        self.user_repository = user_repository
        self.mqtt_service = mqtt_service
        self.device_communication_service = device_communication_service
    
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
            
        Returns:
            AccessValidationResult with access decision and details
            
        Raises:
            EntityNotFoundError: If card or door not found
            InvalidCardError: If card is inactive or invalid
            InvalidDoorError: If door is inactive or invalid
            AccessDeniedError: If access is denied for any reason
        """
        timestamp = datetime.now(timezone.utc)
        logger.info(f"Access validation request: card={card_id}, door={door_id}")
        
        try:
            # 1. Validate card exists and is active
            card = await self.card_repository.get_by_card_id(card_id)
            if not card:
                await self._log_access_attempt(card_id, door_id, False, "Card not found")
                raise EntityNotFoundError(f"Card {card_id} not found")
            
            if not card.is_active():
                await self._log_access_attempt(card_id, door_id, False, "Card inactive")
                raise InvalidCardError(f"Card {card_id} is inactive")
            
            # 2. Validate door exists and is accessible
            door = await self.door_repository.get_by_id(door_id)
            if not door:
                await self._log_access_attempt(card_id, door_id, False, "Door not found")
                raise EntityNotFoundError(f"Door {door_id} not found")
            
            if not door.is_accessible():
                await self._log_access_attempt(card_id, door_id, False, "Door not accessible")
                raise InvalidDoorError(f"Door {door.name} is not accessible")
            
            # 3. Get user information
            user = await self.user_repository.get_by_id(card.user_id)
            if not user:
                await self._log_access_attempt(card_id, door_id, False, "User not found")
                raise EntityNotFoundError(f"User for card {card_id} not found")
            
            if not user.is_active():
                await self._log_access_attempt(card_id, door_id, False, "User inactive")
                raise InvalidCardError(f"User {user.email} is inactive")
            
            # 4. Check if door is locked out due to failed attempts
            if door.is_locked_out():
                await self._log_access_attempt(card_id, door_id, False, "Door locked out")
                raise AccessDeniedError(f"Door {door.name} is temporarily locked due to failed attempts")
            
            # 5. Handle master card access
            if card.is_master_card():
                logger.info(f"Master card access granted: {card_id} to {door.name}")
                await self._record_successful_access(card, door, user)
                
                # Send device response for master card
                if device_id and self.device_communication_service:
                    try:
                        device_response = DeviceAccessResponse.create_granted(
                            reason=f"Master card access granted for {user.full_name}",
                            duration=5,
                            user_name=user.full_name,
                            card_type="master"
                        )
                        await self.device_communication_service.publish_access_response(device_id, device_response)
                        await self.device_communication_service.send_unlock_command(device_id, duration=5)
                    except Exception as device_error:
                        logger.error(f"Failed to communicate with device {device_id}: {device_error}")
                
                return AccessValidationResult(
                    access_granted=True,
                    reason=f"Master card access granted for {user.full_name}",
                    door_name=door.name,
                    user_name=user.full_name,
                    card_type="master",
                    requires_pin=False,
                    card_id=card_id,
                    door_id=door_id,
                    user_id=user.id
                )
            
            # 6. Check permissions for regular cards
            has_permission = await self.permission_repository.check_access(
                user_id=user.id,
                door_id=door_id,
                current_time=timestamp.time(),
                current_day=timestamp.strftime('%a').lower()
            )
            
            if not has_permission:
                await self._log_access_attempt(card_id, door_id, False, "No permission")
                raise AccessDeniedError(f"User {user.full_name} does not have permission to access {door.name}")
            
            # 7. Check PIN requirement for high-security doors
            if door.requires_master_access() and not pin:
                await self._log_access_attempt(card_id, door_id, False, "PIN required")
                
                # Send device response for PIN requirement
                if device_id and self.device_communication_service:
                    try:
                        device_response = DeviceAccessResponse.create_denied(
                            reason=f"PIN required for high-security door {door.name}",
                            requires_pin=True
                        )
                        await self.device_communication_service.publish_access_response(device_id, device_response)
                    except Exception as device_error:
                        logger.error(f"Failed to communicate with device {device_id}: {device_error}")
                
                return AccessValidationResult(
                    access_granted=False,
                    reason=f"PIN required for high-security door {door.name}",
                    door_name=door.name,
                    user_name=user.full_name,
                    card_type=card.card_type.value,
                    requires_pin=True,
                    card_id=card_id,
                    door_id=door_id,
                    user_id=user.id
                )
            
            # 8. Validate PIN if provided
            if pin and not self._validate_pin(pin, user, door):
                await self._log_access_attempt(card_id, door_id, False, "Invalid PIN")
                raise AccessDeniedError("Invalid PIN provided")
            
            # 9. Get permission for additional information (like valid_until)
            permission = await self.permission_repository.get_by_user_and_door(user.id, door_id)
            
            # 10. Grant access - record successful access
            await self._record_successful_access(card, door, user)
            
            # 11. Get valid until time from permission
            valid_until = None
            if permission and permission.valid_until:
                valid_until = permission.valid_until.strftime('%H:%M')
            
            # 12. Send device response if device_id provided
            if device_id and self.device_communication_service:
                try:
                    device_response = DeviceAccessResponse.create_granted(
                        reason=f"Access granted for {user.full_name}",
                        duration=5,  # Unlock for 5 seconds
                        user_name=user.full_name,
                        card_type=card.card_type.value
                    )
                    await self.device_communication_service.publish_access_response(device_id, device_response)
                    
                    # Send unlock command
                    await self.device_communication_service.send_unlock_command(device_id, duration=5)
                except Exception as device_error:
                    logger.error(f"Failed to communicate with device {device_id}: {device_error}")
            
            logger.info(f"Access granted: {card_id} to {door.name} for {user.full_name}")
            
            return AccessValidationResult(
                access_granted=True,
                reason=f"Access granted for {user.full_name}",
                door_name=door.name,
                user_name=user.full_name,
                card_type=card.card_type.value,
                requires_pin=door.requires_master_access(),
                valid_until=valid_until,
                card_id=card_id,
                door_id=door_id,
                user_id=user.id
            )
            
        except Exception as e:
            logger.error(f"Error validating access: {str(e)}")
            await self._log_access_attempt(card_id, door_id, False, str(e))
            
            # Send denial response to device if device_id provided
            if device_id and self.device_communication_service:
                try:
                    device_response = DeviceAccessResponse.create_denied(reason=str(e))
                    await self.device_communication_service.publish_access_response(device_id, device_response)
                except Exception as device_error:
                    logger.error(f"Failed to send device response: {device_error}")
            
            raise
    
    async def _record_successful_access(self, card, door, user):
        """Record successful access attempt."""
        # Update card usage
        card.record_usage()
        await self.card_repository.update(card)
        
        # Update door access
        door.record_successful_access(user.id)
        await self.door_repository.update(door)
        
        # Log successful access
        await self._log_access_attempt(
            card.card_id, 
            door.id, 
            True, 
            f"Access granted for {user.full_name}"
        )
    
    async def _log_access_attempt(self, card_id: str, door_id: UUID, success: bool, reason: str):
        """Log access attempt via MQTT."""
        try:
            import json
            payload = {
    			"card_id": str(card_id),  # UUID as string
    			"door_id": str(door_id),
                "result": "granted" if success else "denied",
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            message = MqttMessage(
                topic=f"access/door_{door_id}/attempts",
                message=json.dumps(payload),
                timestamp=datetime.now(timezone.utc)
            )
            await self.mqtt_service.save_message(message)
        except Exception as e:
            logger.error(f"Failed to log access attempt: {str(e)}")
    
    def _validate_pin(self, pin: str, user, door) -> bool:
        """Validate PIN code (simple implementation)."""
        # In a real system, this would check against a secure PIN database
        # For now, accept any 4-8 digit PIN as valid
        return pin.isdigit() and 4 <= len(pin) <= 8