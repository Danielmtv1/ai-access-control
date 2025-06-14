"""
Tests for device communication service.
"""
import pytest
import json
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timezone, timedelta , timezone
from uuid import uuid4, UUID

from app.domain.services.device_communication_service import DeviceCommunicationService
from app.domain.entities.device_message import (
    DeviceAccessRequest,
    DeviceAccessResponse,
    DoorCommand,
    DeviceStatus,
    DeviceEvent,
    CommandAcknowledgment,
    DeviceCommandType,
    DoorAction
)


@pytest.fixture
def mock_mqtt_adapter():
    """Mock MQTT adapter for testing."""
    adapter = AsyncMock()
    adapter.publish = AsyncMock(return_value=None)
    return adapter


@pytest.fixture
def device_service(mock_mqtt_adapter):
    """Device communication service with mocked MQTT adapter."""
    return DeviceCommunicationService(mock_mqtt_adapter)


class TestDeviceCommunicationService:
    """Tests for DeviceCommunicationService."""
    
    @pytest.mark.asyncio
    async def test_publish_access_response_granted(self, device_service, mock_mqtt_adapter):
        """Test publishing granted access response."""
        device_id = "door_lock_001"
        response = DeviceAccessResponse.create_granted(
            reason="Access granted for John Doe",
            duration=5,
            user_name="John Doe",
            card_type="employee"
        )
        
        result = await device_service.publish_access_response(device_id, response)
        
        assert result is True
        mock_mqtt_adapter.publish.assert_called_once()
        
        # Verify the topic and payload
        call_args = mock_mqtt_adapter.publish.call_args
        topic = call_args[0][0]
        payload_str = call_args[0][1]
        qos = call_args[1]['qos']
        
        assert topic == f"access/responses/{device_id}"
        assert qos == 2
        
        payload = json.loads(payload_str)
        assert payload["access_granted"] is True
        assert payload["door_action"] == "unlock"
        assert payload["reason"] == "Access granted for John Doe"
        assert payload["duration"] == 5
        assert payload["user_name"] == "John Doe"
        assert payload["card_type"] == "employee"
        assert payload["requires_pin"] is False
        assert "message_id" in payload
        assert "timestamp" in payload
    
    @pytest.mark.asyncio
    async def test_publish_access_response_denied(self, device_service, mock_mqtt_adapter):
        """Test publishing denied access response."""
        device_id = "door_lock_002"
        response = DeviceAccessResponse.create_denied(
            reason="Card not found",
            requires_pin=False
        )
        
        result = await device_service.publish_access_response(device_id, response)
        
        assert result is True
        mock_mqtt_adapter.publish.assert_called_once()
        
        call_args = mock_mqtt_adapter.publish.call_args
        payload_str = call_args[0][1]
        payload = json.loads(payload_str)
        
        assert payload["access_granted"] is False
        assert payload["door_action"] == "deny"
        assert payload["reason"] == "Card not found"
        assert payload["requires_pin"] is False
    
    @pytest.mark.asyncio
    async def test_publish_access_response_mqtt_error(self, device_service, mock_mqtt_adapter):
        """Test handling MQTT publish error for access response."""
        mock_mqtt_adapter.publish.side_effect = Exception("MQTT connection failed")
        
        device_id = "door_lock_001"
        response = DeviceAccessResponse.create_granted(reason="Test")
        
        result = await device_service.publish_access_response(device_id, response)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_door_command_unlock(self, device_service, mock_mqtt_adapter):
        """Test sending unlock command to door."""
        command = DoorCommand.create_unlock("door_lock_001", duration=10)
        
        result = await device_service.send_door_command(command)
        
        assert result is True
        mock_mqtt_adapter.publish.assert_called_once()
        
        call_args = mock_mqtt_adapter.publish.call_args
        topic = call_args[0][0]
        payload_str = call_args[0][1]
        qos = call_args[1]['qos']
        
        assert topic == "access/commands/door_lock_001"
        assert qos == 2
        
        payload = json.loads(payload_str)
        assert payload["command"] == "unlock"
        assert payload["parameters"]["duration"] == 10
        assert payload["timeout"] == 30
        assert payload["requires_ack"] is True
        assert "message_id" in payload
        assert "timestamp" in payload
    
    @pytest.mark.asyncio
    async def test_send_door_command_with_acknowledgment_tracking(self, device_service, mock_mqtt_adapter):
        """Test sending command with acknowledgment tracking."""
        command = DoorCommand.create_lock("door_lock_001")
        
        result = await device_service.send_door_command(command)
        
        assert result is True
        
        # Verify command is tracked in pending commands
        pending_commands = device_service.get_pending_commands()
        assert command.message_id in pending_commands
        assert pending_commands[command.message_id] == command
    
    @pytest.mark.asyncio
    async def test_send_door_command_without_acknowledgment(self, device_service, mock_mqtt_adapter):
        """Test sending command without acknowledgment requirement."""
        command = DoorCommand(
            command=DeviceCommandType.STATUS,
            device_id="door_lock_001",
            message_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc),
            parameters={},
            requires_ack=False
        )
        
        result = await device_service.send_door_command(command)
        
        assert result is True
        
        # Verify command is not tracked when ack not required
        pending_commands = device_service.get_pending_commands()
        assert command.message_id not in pending_commands
    
    @pytest.mark.asyncio
    async def test_send_unlock_command_shortcut(self, device_service, mock_mqtt_adapter):
        """Test unlock command shortcut method."""
        device_id = "door_lock_001"
        duration = 7
        
        result = await device_service.send_unlock_command(device_id, duration)
        
        assert result is True
        mock_mqtt_adapter.publish.assert_called_once()
        
        call_args = mock_mqtt_adapter.publish.call_args
        payload_str = call_args[0][1]
        payload = json.loads(payload_str)
        
        assert payload["command"] == "unlock"
        assert payload["parameters"]["duration"] == duration
    
    @pytest.mark.asyncio
    async def test_send_lock_command_shortcut(self, device_service, mock_mqtt_adapter):
        """Test lock command shortcut method."""
        device_id = "door_lock_002"
        
        result = await device_service.send_lock_command(device_id)
        
        assert result is True
        mock_mqtt_adapter.publish.assert_called_once()
        
        call_args = mock_mqtt_adapter.publish.call_args
        payload_str = call_args[0][1]
        payload = json.loads(payload_str)
        
        assert payload["command"] == "lock"
        assert payload["parameters"] == {}
    
    @pytest.mark.asyncio
    async def test_request_device_status(self, device_service, mock_mqtt_adapter):
        """Test requesting device status."""
        device_id = "door_lock_003"
        
        result = await device_service.request_device_status(device_id)
        
        assert result is True
        mock_mqtt_adapter.publish.assert_called_once()
        
        call_args = mock_mqtt_adapter.publish.call_args
        payload_str = call_args[0][1]
        payload = json.loads(payload_str)
        
        assert payload["command"] == "status"
        assert payload["requires_ack"] is True
    
    @pytest.mark.asyncio
    async def test_broadcast_notification(self, device_service, mock_mqtt_adapter):
        """Test broadcasting notification to all devices."""
        message = "System maintenance in 10 minutes"
        severity = "warning"
        
        result = await device_service.broadcast_notification(message, severity)
        
        assert result is True
        mock_mqtt_adapter.publish.assert_called_once()
        
        call_args = mock_mqtt_adapter.publish.call_args
        topic = call_args[0][0]
        payload_str = call_args[0][1]
        qos = call_args[1]['qos']
        
        assert topic == "access/notifications/broadcast"
        assert qos == 1
        
        payload = json.loads(payload_str)
        assert payload["message"] == message
        assert payload["severity"] == severity
        assert "timestamp" in payload
        assert "message_id" in payload
    
    @pytest.mark.asyncio
    async def test_emergency_lockdown(self, device_service, mock_mqtt_adapter):
        """Test emergency lockdown command."""
        reason = "Security breach detected"
        
        result = await device_service.handle_emergency_lockdown(reason)
        
        assert result is True
        mock_mqtt_adapter.publish.assert_called_once()
        
        call_args = mock_mqtt_adapter.publish.call_args
        topic = call_args[0][0]
        payload_str = call_args[0][1]
        qos = call_args[1]['qos']
        
        assert topic == "access/commands/emergency/lockdown"
        assert qos == 2
        
        payload = json.loads(payload_str)
        assert payload["command"] == "emergency_lock"
        assert payload["reason"] == reason
        assert "timestamp" in payload
        assert "message_id" in payload


class TestDeviceMessageParsing:
    """Tests for device message parsing methods."""
    TEST_DOOR_ID = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d483")
    TEST_USER_ID = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")

    @pytest.mark.asyncio
    async def test_parse_device_request_valid(self, device_service):
        """Test parsing valid device access request."""
        topic = "access/requests/door_lock_001"
        payload = json.dumps({
            "card_id": "ABC123",
            "door_id": str(self.TEST_DOOR_ID),  # Match the device_id expected by the parser
            "pin": "1234",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_id": str(uuid4()),
            "location_data": {"floor": 2, "room": "201"}
        })
        
        request = device_service.parse_device_request(topic, payload)
        print(f"Request result: {request}") 
        # assert request is not None
        assert request.card_id == "ABC123"
        assert request.door_id == self.TEST_DOOR_ID
        assert request.device_id == "door_lock_001"
        assert request.pin == "1234"
        assert request.location_data["floor"] == 2
    
    def test_parse_device_request_missing_required_field(self, device_service):
        """Test parsing device request with missing required field."""
        topic = "access/requests/door_lock_001"
        payload = json.dumps({
            "card_id": "ABC123"
            # Missing door_id
        })
        
        request = device_service.parse_device_request(topic, payload)
        
        assert request is None
    
    def test_parse_device_request_invalid_topic(self, device_service):
        """Test parsing device request with invalid topic format."""
        topic = "invalid/topic"
        payload = json.dumps({"card_id": "ABC123", "door_id": str(self.TEST_DOOR_ID)})
        
        request = device_service.parse_device_request(topic, payload)
        
        assert request is None
    
    def test_parse_device_request_invalid_json(self, device_service):
        """Test parsing device request with invalid JSON."""
        topic = "access/requests/door_lock_001"
        payload = "invalid json"
        
        request = device_service.parse_device_request(topic, payload)
        
        assert request is None
    
    def test_parse_command_acknowledgment_valid(self, device_service):
        """Test parsing valid command acknowledgment."""
        topic = "access/commands/door_lock_001/ack"
        message_id = str(uuid4())
        payload = json.dumps({
            "message_id": message_id,
            "status": "success",
            "result": {"door_state": "unlocked"},
            "execution_time": 0.5,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Add a pending command to be acknowledged
        command = DoorCommand.create_unlock("door_lock_001")
        command.message_id = message_id
        device_service._pending_commands[message_id] = command
        
        ack = device_service.parse_command_acknowledgment(topic, payload)
        
        assert ack is not None
        assert ack.message_id == message_id
        assert ack.device_id == "door_lock_001"
        assert ack.status == "success"
        assert ack.result["door_state"] == "unlocked"
        assert ack.execution_time == 0.5
        
        # Verify command was removed from pending
        assert message_id not in device_service._pending_commands
    
    def test_parse_command_acknowledgment_invalid_topic(self, device_service):
        """Test parsing acknowledgment with invalid topic."""
        topic = "invalid/topic"
        payload = json.dumps({"message_id": str(uuid4()), "status": "success"})
        
        ack = device_service.parse_command_acknowledgment(topic, payload)
        
        assert ack is None
    
    def test_parse_device_status_valid(self, device_service):
        """Test parsing valid device status."""
        topic = "access/devices/door_lock_001/status"
        payload = json.dumps({
            "online": True,
            "door_state": "locked",
            "battery_level": 75,
            "signal_strength": -55,
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
            "firmware_version": "1.2.3"
        })
        
        status = device_service.parse_device_status(topic, payload)
        
        assert status is not None
        assert status.device_id == "door_lock_001"
        assert status.online is True
        assert status.door_state == "locked"
        assert status.battery_level == 75
        assert status.signal_strength == -55
        assert status.firmware_version == "1.2.3"
    
    def test_parse_device_event_with_type_in_topic(self, device_service):
        """Test parsing device event with type in topic."""
        topic = "access/events/door_forced/door_lock_001"
        payload = json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_id": str(uuid4()),
            "details": {"force_detected": True},
            "severity": "critical"
        })
        
        event = device_service.parse_device_event(topic, payload)
        
        assert event is not None
        assert event.device_id == "door_lock_001"
        assert event.event_type == "door_forced"
        assert event.details["force_detected"] is True
        assert event.severity == "critical"
    
    def test_parse_device_event_without_type_in_topic(self, device_service):
        """Test parsing device event without type in topic."""
        topic = "access/events/door_lock_001"
        payload = json.dumps({
            "event_type": "door_opened",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {"card_id": "ABC123"},
            "severity": "info"
        })
        
        event = device_service.parse_device_event(topic, payload)
        
        assert event is not None
        assert event.device_id == "door_lock_001"
        assert event.event_type == "door_opened"
        assert event.details["card_id"] == "ABC123"
        assert event.severity == "info"


class TestCommandManagement:
    """Tests for command management functionality."""
    
    def test_get_pending_commands_empty(self, device_service):
        """Test getting pending commands when none exist."""
        pending = device_service.get_pending_commands()
        
        assert pending == {}
    
    def test_get_pending_commands_with_commands(self, device_service):
        """Test getting pending commands when some exist."""
        command1 = DoorCommand.create_unlock("door_lock_001")
        command2 = DoorCommand.create_lock("door_lock_002")
        
        device_service._pending_commands[command1.message_id] = command1
        device_service._pending_commands[command2.message_id] = command2
        
        pending = device_service.get_pending_commands()
        
        assert len(pending) == 2
        assert command1.message_id in pending
        assert command2.message_id in pending
        assert pending[command1.message_id] == command1
        assert pending[command2.message_id] == command2
    
    def test_cleanup_expired_commands(self, device_service):
        """Test cleanup of expired commands."""
        # Create commands with different timestamps
        recent_command = DoorCommand.create_unlock("door_lock_001")
        old_command = DoorCommand.create_lock("door_lock_002")
        
        # Make one command appear old
        old_timestamp = datetime.now(timezone.utc).replace(year=2020)  # Very old timestamp
        old_command.timestamp = old_timestamp
        
        device_service._pending_commands[recent_command.message_id] = recent_command
        device_service._pending_commands[old_command.message_id] = old_command
        
        # Cleanup with 1 second max age (recent command should remain)
        device_service.cleanup_expired_commands(max_age_seconds=1)
        
        pending = device_service.get_pending_commands()
        assert recent_command.message_id in pending
        assert old_command.message_id not in pending