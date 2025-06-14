"""
Domain service for IoT device communication via MQTT.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Callable
from uuid import UUID, uuid4

from app.domain.entities.device_message import (
    DeviceAccessRequest, 
    DeviceAccessResponse, 
    DoorCommand, 
    DeviceStatus,
    DeviceEvent,
    CommandAcknowledgment,
    DoorAction
)
from app.infrastructure.mqtt.adapters.asyncio_mqtt_adapter import AiomqttAdapter
from app.config import get_settings

logger = logging.getLogger(__name__)


class DeviceCommunicationService:
    """Service for managing bidirectional MQTT communication with IoT devices."""
    
    def __init__(self, mqtt_adapter: AiomqttAdapter):
        self.mqtt_adapter = mqtt_adapter
        self._command_callbacks: Dict[str, Callable] = {}
        self._pending_commands: Dict[str, DoorCommand] = {}
    
    async def publish_access_response(self, device_id: str, response: DeviceAccessResponse) -> bool:
        """Send access validation response to IoT device."""
        try:
            topic = f"access/responses/{device_id}"
            payload = {
                "access_granted": response.access_granted,
                "door_action": response.door_action.value,
                "reason": response.reason,
                "duration": response.duration,
                "user_name": response.user_name,
                "card_type": response.card_type,
                "requires_pin": response.requires_pin,
                "message_id": response.message_id,
                "timestamp": response.timestamp.isoformat()
            }
            
            await self.mqtt_adapter.publish(topic, json.dumps(payload), qos=2)
            logger.info(f"Access response sent to device {device_id}: {response.access_granted}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send access response to device {device_id}: {str(e)}")
            return False
    
    async def send_door_command(self, command: DoorCommand) -> bool:
        """Send command to door device."""
        try:
            topic = f"access/commands/{command.device_id}"
            payload = {
                "command": command.command.value,
                "parameters": command.parameters,
                "message_id": command.message_id,
                "timestamp": command.timestamp.isoformat(),
                "timeout": command.timeout,
                "requires_ack": command.requires_ack
            }
            
            # Store command for acknowledgment tracking
            if command.requires_ack:
                self._pending_commands[command.message_id] = command
            
            await self.mqtt_adapter.publish(topic, json.dumps(payload), qos=2)
            logger.info(f"Command {command.command.value} sent to device {command.device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send command to device {command.device_id}: {str(e)}")
            return False
    
    async def send_unlock_command(self, device_id: str, duration: int = None) -> bool:
        """Send unlock command to specific device."""
        if duration is None:
            duration = get_settings().DEFAULT_UNLOCK_DURATION
        command = DoorCommand.create_unlock(device_id, duration)
        return await self.send_door_command(command)
    
    async def send_lock_command(self, device_id: str) -> bool:
        """Send lock command to specific device."""
        command = DoorCommand.create_lock(device_id)
        return await self.send_door_command(command)
    
    async def request_device_status(self, device_id: str) -> bool:
        """Request status from specific device."""
        command = DoorCommand.create_status_request(device_id)
        return await self.send_door_command(command)
    
    async def broadcast_notification(self, message: str, severity: str = "info") -> bool:
        """Broadcast notification to all devices."""
        try:
            topic = "access/notifications/broadcast"
            payload = {
                "message": message,
                "severity": severity,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message_id": str(uuid4())
            }
            
            await self.mqtt_adapter.publish(topic, json.dumps(payload), qos=1)
            logger.info(f"Broadcast notification sent: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send broadcast notification: {str(e)}")
            return False
    
    def parse_device_request(self, topic: str, payload: str) -> Optional[DeviceAccessRequest]:
        """Parse incoming access request from device."""
        try:
            # Extract device_id from topic: access/requests/{device_id}
            topic_parts = topic.split('/')
            if len(topic_parts) < 3:
                logger.warning(f"Invalid request topic format: {topic}")
                return None
            
            device_id = topic_parts[2]
            data = json.loads(payload)
            
            # Validate required fields
            required_fields = ['card_id', 'door_id']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing required field {field} in device request")
                    return None
            
            return DeviceAccessRequest(
                card_id=data['card_id'],
                door_id=UUID(data['door_id']),
                device_id=device_id,
                pin=data.get('pin'),
                timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now(timezone.utc).isoformat())),
                message_id=data.get('message_id', str(uuid4())),
                location_data=data.get('location_data')
            )
            
        except Exception as e:
            logger.error(f"Failed to parse device request from {topic}: {str(e)}")
            return None
    
    def parse_command_acknowledgment(self, topic: str, payload: str) -> Optional[CommandAcknowledgment]:
        """Parse command acknowledgment from device."""
        try:
            # Extract device_id from topic: access/commands/{device_id}/ack
            topic_parts = topic.split('/')
            if len(topic_parts) < 4:
                logger.warning(f"Invalid ack topic format: {topic}")
                return None
            
            device_id = topic_parts[2]
            data = json.loads(payload)
            
            ack = CommandAcknowledgment(
                message_id=data['message_id'],
                device_id=device_id,
                status=data['status'],
                result=data.get('result'),
                error_message=data.get('error_message'),
                execution_time=data.get('execution_time'),
                timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now(timezone.utc).isoformat()))
            )
            
            # Remove from pending commands if acknowledged
            if ack.message_id in self._pending_commands:
                del self._pending_commands[ack.message_id]
                logger.info(f"Command {ack.message_id} acknowledged by device {device_id}: {ack.status}")
            
            return ack
            
        except Exception as e:
            logger.error(f"Failed to parse command acknowledgment from {topic}: {str(e)}")
            return None
    
    def parse_device_status(self, topic: str, payload: str) -> Optional[DeviceStatus]:
        """Parse device status update."""
        try:
            # Extract device_id from topic: access/devices/{device_id}/status
            topic_parts = topic.split('/')
            if len(topic_parts) < 4:
                logger.warning(f"Invalid status topic format: {topic}")
                return None
            
            device_id = topic_parts[2]
            data = json.loads(payload)
            
            return DeviceStatus(
                device_id=device_id,
                online=data.get('online', True),
                door_state=data.get('door_state', 'unknown'),
                battery_level=data.get('battery_level'),
                signal_strength=data.get('signal_strength'),
                last_heartbeat=datetime.fromisoformat(data.get('last_heartbeat', datetime.now(timezone.utc).isoformat())),
                error_message=data.get('error_message'),
                firmware_version=data.get('firmware_version')
            )
            
        except Exception as e:
            logger.error(f"Failed to parse device status from {topic}: {str(e)}")
            return None
    
    def parse_device_event(self, topic: str, payload: str) -> Optional[DeviceEvent]:
        """Parse device event."""
        try:
            # Extract info from topic: access/events/{type}/{device_id} or access/events/{device_id}
            topic_parts = topic.split('/')
            if len(topic_parts) < 3:
                logger.warning(f"Invalid event topic format: {topic}")
                return None
            
            data = json.loads(payload)
            
            # Determine device_id and event_type based on topic structure
            if len(topic_parts) == 4:  # access/events/{type}/{device_id}
                event_type = topic_parts[2]
                device_id = topic_parts[3]
            else:  # access/events/{device_id}
                device_id = topic_parts[2]
                event_type = data.get('event_type', 'generic')
            
            return DeviceEvent(
                device_id=device_id,
                event_type=event_type,
                timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now(timezone.utc).isoformat())),
                message_id=data.get('message_id', str(uuid4())),
                details=data.get('details', {}),
                severity=data.get('severity', 'info')
            )
            
        except Exception as e:
            logger.error(f"Failed to parse device event from {topic}: {str(e)}")
            return None
    
    def get_pending_commands(self) -> Dict[str, DoorCommand]:
        """Get list of pending commands awaiting acknowledgment."""
        return self._pending_commands.copy()
    
    def cleanup_expired_commands(self, max_age_seconds: int = None):
        """Remove commands that have been pending too long."""
        if max_age_seconds is None:
            max_age_seconds = get_settings().MQTT_COMMAND_CLEANUP_SECONDS
        current_time = datetime.now(timezone.utc)
        expired_commands = []
        
        for message_id, command in self._pending_commands.items():
            age = (current_time - command.timestamp).total_seconds()
            if age > max_age_seconds:
                expired_commands.append(message_id)
        
        for message_id in expired_commands:
            del self._pending_commands[message_id]
            logger.warning(f"Command {message_id} expired after {max_age_seconds} seconds")
    
    async def handle_emergency_lockdown(self, reason: str) -> bool:
        """Trigger emergency lockdown for all devices."""
        try:
            topic = "access/commands/emergency/lockdown"
            payload = {
                "command": "emergency_lock",
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message_id": str(uuid4())
            }
            
            await self.mqtt_adapter.publish(topic, json.dumps(payload), qos=2)
            logger.critical(f"Emergency lockdown initiated: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initiate emergency lockdown: {str(e)}")
            return False