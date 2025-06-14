"""
MQTT device message handler for processing IoT device communications.
"""
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.domain.services.device_communication_service import DeviceCommunicationService
from app.application.use_cases.access_use_cases import ValidateAccessUseCase
from app.domain.entities.device_message import (
    DeviceAccessRequest, 
    CommandAcknowledgment, 
    DeviceStatus, 
    DeviceEvent
)
from app.domain.services.mqtt_message_service import MqttMessageService
from app.domain.entities.mqtt_message import MqttMessage

logger = logging.getLogger(__name__)


class MqttDeviceHandler:
    """Handler for processing MQTT messages from IoT devices."""
    
    def __init__(
        self,
        device_communication_service: DeviceCommunicationService,
        access_validation_use_case: ValidateAccessUseCase,
        mqtt_message_service: MqttMessageService
    ):
        self.device_service = device_communication_service
        self.access_use_case = access_validation_use_case
        self.mqtt_service = mqtt_message_service
    
    async def handle_message(self, topic: str, payload: str) -> None:
        """
        Route MQTT messages to appropriate handlers based on topic structure.
        
        Topic patterns:
        - access/requests/{device_id} -> Access validation requests
        - access/commands/{device_id}/ack -> Command acknowledgments
        - access/devices/{device_id}/status -> Device status updates
        - access/events/{type}/{device_id} -> Device events
        """
        try:
            # Log all incoming messages
            await self._log_message(topic, payload)
            
            # Parse topic structure
            topic_parts = topic.split('/')
            if len(topic_parts) < 2:
                logger.warning(f"Invalid topic structure: {topic}")
                return
            
            # Route based on topic pattern
            if topic_parts[0] == "access":
                if len(topic_parts) >= 3:
                    if topic_parts[1] == "requests":
                        await self._handle_access_request(topic, payload)
                    elif topic_parts[1] == "commands" and len(topic_parts) >= 4 and topic_parts[3] == "ack":
                        await self._handle_command_acknowledgment(topic, payload)
                    elif topic_parts[1] == "devices" and len(topic_parts) >= 4 and topic_parts[3] == "status":
                        await self._handle_device_status(topic, payload)
                    elif topic_parts[1] == "events":
                        await self._handle_device_event(topic, payload)
                    else:
                        logger.debug(f"Unhandled access topic: {topic}")
                else:
                    logger.debug(f"Incomplete access topic: {topic}")
            else:
                logger.debug(f"Non-access topic: {topic}")
                
        except Exception as e:
            logger.error(f"Error handling MQTT message from {topic}: {str(e)}", exc_info=True)
    
    async def _handle_access_request(self, topic: str, payload: str) -> None:
        """Handle access validation requests from devices."""
        try:
            # Parse device request
            device_request = self.device_service.parse_device_request(topic, payload)
            if not device_request:
                logger.warning(f"Failed to parse device request from {topic}")
                return
            
            logger.info(f"Processing access request from device {device_request.device_id}")
            
            # Validate access using the use case
            try:
                result = await self.access_use_case.execute(
                    card_id=device_request.card_id,
                    door_id=device_request.door_id,
                    pin=device_request.pin,
                    device_id=device_request.device_id
                )
                
                logger.info(f"Access validation completed for device {device_request.device_id}: {result.access_granted}")
                
            except Exception as validation_error:
                logger.error(f"Access validation failed for device {device_request.device_id}: {str(validation_error)}")
                # Device response is already sent by the use case exception handler
                
        except Exception as e:
            logger.error(f"Error processing access request: {str(e)}")
    
    async def _handle_command_acknowledgment(self, topic: str, payload: str) -> None:
        """Handle command acknowledgments from devices."""
        try:
            ack = self.device_service.parse_command_acknowledgment(topic, payload)
            if not ack:
                logger.warning(f"Failed to parse command acknowledgment from {topic}")
                return
            
            logger.info(f"Command {ack.message_id} acknowledged by device {ack.device_id}: {ack.status}")
            
            # Log acknowledgment for audit trail
            await self._log_command_acknowledgment(ack)
            
            # Handle failed commands
            if not ack.is_successful():
                logger.warning(f"Command {ack.message_id} failed on device {ack.device_id}: {ack.error_message}")
                await self._handle_failed_command(ack)
            
        except Exception as e:
            logger.error(f"Error processing command acknowledgment: {str(e)}")
    
    async def _handle_device_status(self, topic: str, payload: str) -> None:
        """Handle device status updates."""
        try:
            status = self.device_service.parse_device_status(topic, payload)
            if not status:
                logger.warning(f"Failed to parse device status from {topic}")
                return
            
            logger.info(f"Device {status.device_id} status: online={status.online}, door_state={status.door_state}")
            
            # Log status for monitoring
            await self._log_device_status(status)
            
            # Check for alerts
            if not status.is_healthy():
                await self._handle_device_alert(status)
            
        except Exception as e:
            logger.error(f"Error processing device status: {str(e)}")
    
    async def _handle_device_event(self, topic: str, payload: str) -> None:
        """Handle device events (security alerts, door forced, etc.)."""
        try:
            event = self.device_service.parse_device_event(topic, payload)
            if not event:
                logger.warning(f"Failed to parse device event from {topic}")
                return
            
            logger.info(f"Device {event.device_id} event: {event.event_type} (severity: {event.severity})")
            
            # Log event for audit
            await self._log_device_event(event)
            
            # Handle critical events
            if event.severity in ["critical", "error"]:
                await self._handle_critical_event(event)
            
        except Exception as e:
            logger.error(f"Error processing device event: {str(e)}")
    
    async def _log_message(self, topic: str, payload: str) -> None:
        """Log incoming MQTT message."""
        try:
            message = MqttMessage(
                topic=topic,
                message=payload,
                timestamp=datetime.now(timezone.utc)
            )
            await self.mqtt_service.process_message(message)
        except Exception as e:
            logger.error(f"Failed to log MQTT message: {str(e)}")
    
    async def _log_command_acknowledgment(self, ack: CommandAcknowledgment) -> None:
        """Log command acknowledgment for audit trail."""
        try:
            log_data = {
                "event_type": "command_acknowledgment",
                "device_id": ack.device_id,
                "message_id": ack.message_id,
                "status": ack.status,
                "execution_time": ack.execution_time,
                "timestamp": ack.timestamp.isoformat() if ack.timestamp else datetime.now(timezone.utc).isoformat()
            }
            
            message = MqttMessage(
                topic=f"audit/commands/{ack.device_id}/ack",
                message=json.dumps(log_data),
                timestamp=datetime.now(timezone.utc)
            )
            await self.mqtt_service.process_message(message)
        except Exception as e:
            logger.error(f"Failed to log command acknowledgment: {str(e)}")
    
    async def _log_device_status(self, status: DeviceStatus) -> None:
        """Log device status for monitoring."""
        try:
            log_data = {
                "event_type": "device_status",
                "device_id": status.device_id,
                "online": status.online,
                "door_state": status.door_state,
                "battery_level": status.battery_level,
                "signal_strength": status.signal_strength,
                "is_healthy": status.is_healthy(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            message = MqttMessage(
                topic=f"monitoring/devices/{status.device_id}/status",
                message=json.dumps(log_data),
                timestamp=datetime.now(timezone.utc)
            )
            await self.mqtt_service.process_message(message)
        except Exception as e:
            logger.error(f"Failed to log device status: {str(e)}")
    
    async def _log_device_event(self, event: DeviceEvent) -> None:
        """Log device event for audit trail."""
        try:
            log_data = {
                "event_type": event.event_type,
                "device_id": event.device_id,
                "severity": event.severity,
                "details": event.details,
                "message_id": event.message_id,
                "timestamp": event.timestamp.isoformat()
            }
            
            message = MqttMessage(
                topic=f"audit/events/{event.device_id}/{event.event_type}",
                message=json.dumps(log_data),
                timestamp=datetime.now(timezone.utc)
            )
            await self.mqtt_service.process_message(message)
        except Exception as e:
            logger.error(f"Failed to log device event: {str(e)}")
    
    async def _handle_failed_command(self, ack: CommandAcknowledgment) -> None:
        """Handle failed command execution."""
        logger.warning(f"Handling failed command {ack.message_id} on device {ack.device_id}")
        
        # Could implement retry logic, notifications, etc.
        # For now, just log the failure
        try:
            alert_data = {
                "alert_type": "command_failed",
                "device_id": ack.device_id,
                "message_id": ack.message_id,
                "error": ack.error_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            message = MqttMessage(
                topic=f"alerts/commands/{ack.device_id}/failed",
                message=json.dumps(alert_data),
                timestamp=datetime.now(timezone.utc)
            )
            await self.mqtt_service.process_message(message)
        except Exception as e:
            logger.error(f"Failed to handle failed command: {str(e)}")
    
    async def _handle_device_alert(self, status: DeviceStatus) -> None:
        """Handle device health alerts."""
        logger.warning(f"Device {status.device_id} health alert: {status.error_message}")
        
        try:
            alert_data = {
                "alert_type": "device_health",
                "device_id": status.device_id,
                "battery_level": status.battery_level,
                "signal_strength": status.signal_strength,
                "error_message": status.error_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            message = MqttMessage(
                topic=f"alerts/devices/{status.device_id}/health",
                message=json.dumps(alert_data),
                timestamp=datetime.now(timezone.utc)
            )
            await self.mqtt_service.process_message(message)
        except Exception as e:
            logger.error(f"Failed to handle device alert: {str(e)}")
    
    async def _handle_critical_event(self, event: DeviceEvent) -> None:
        """Handle critical security events."""
        logger.critical(f"Critical event from device {event.device_id}: {event.event_type}")
        
        try:
            # Log critical event
            alert_data = {
                "alert_type": "critical_security_event",
                "device_id": event.device_id,
                "event_type": event.event_type,
                "severity": event.severity,
                "details": event.details,
                "timestamp": event.timestamp.isoformat()
            }
            
            message = MqttMessage(
                topic=f"alerts/security/{event.device_id}/critical",
                message=json.dumps(alert_data),
                timestamp=datetime.now(timezone.utc)
            )
            await self.mqtt_service.process_message(message)
            
            # Handle specific critical events
            if event.event_type == "door_forced":
                await self._handle_door_forced_event(event)
            elif event.event_type == "tamper_alert":
                await self._handle_tamper_event(event)
                
        except Exception as e:
            logger.error(f"Failed to handle critical event: {str(e)}")
    
    async def _handle_door_forced_event(self, event: DeviceEvent) -> None:
        """Handle door forced open security event."""
        logger.critical(f"Door forced open on device {event.device_id}")
        
        # Could trigger emergency protocols, notifications, etc.
        # For now, broadcast an alert
        await self.device_service.broadcast_notification(
            f"SECURITY ALERT: Door forced open on device {event.device_id}",
            severity="critical"
        )
    
    async def _handle_tamper_event(self, event: DeviceEvent) -> None:
        """Handle device tamper security event."""
        logger.critical(f"Device tamper detected on {event.device_id}")
        
        # Could trigger emergency lockdown, notifications, etc.
        # For now, broadcast an alert
        await self.device_service.broadcast_notification(
            f"SECURITY ALERT: Device tamper detected on {event.device_id}",
            severity="critical"
        )