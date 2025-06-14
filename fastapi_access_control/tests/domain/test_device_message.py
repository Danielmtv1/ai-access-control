"""
Tests for device message entities.
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

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
from tests.conftest import SAMPLE_CARD_UUID, SAMPLE_CARD_UUID_2, SAMPLE_DOOR_UUID


class TestDeviceCommandType:
    """Tests for DeviceCommandType enum."""
    
    def test_command_type_values(self):
        """
        Verifies that DeviceCommandType enum values match their expected string representations.
        """
        assert DeviceCommandType.UNLOCK.value == "unlock"
        assert DeviceCommandType.LOCK.value == "lock"
        assert DeviceCommandType.STATUS.value == "status"
        assert DeviceCommandType.REBOOT.value == "reboot"
        assert DeviceCommandType.UPDATE_CONFIG.value == "update_config"


class TestDoorAction:
    """Tests for DoorAction enum."""
    
    def test_door_action_values(self):
        """Test door action enum values."""
        assert DoorAction.UNLOCK.value == "unlock"
        assert DoorAction.DENY.value == "deny"
        assert DoorAction.REQUIRE_PIN.value == "require_pin"
        assert DoorAction.ALREADY_OPEN.value == "already_open"


class TestDeviceAccessRequest:
    """Tests for DeviceAccessRequest entity."""
    
    def test_device_access_request_creation(self):
        """
        Verifies that a DeviceAccessRequest is correctly created with all fields assigned as expected.
        """
        timestamp = datetime.now(timezone.utc)
        message_id = str(uuid4())
        
        request = DeviceAccessRequest(
            card_id="ABC123",
            door_id=SAMPLE_DOOR_UUID,
            device_id="door_lock_001",
            timestamp=timestamp,
            message_id=message_id,
            pin="1234",
            location_data={"latitude": 40.7128, "longitude": -74.0060}
        )
        
        assert request.card_id == "ABC123"
        assert request.door_id == SAMPLE_DOOR_UUID
        assert request.device_id == "door_lock_001"
        assert request.timestamp == timestamp
        assert request.message_id == message_id
        assert request.pin == "1234"
        assert request.location_data["latitude"] == 40.7128
    
    def test_device_access_request_factory_method(self):
        """
        Tests the DeviceAccessRequest factory method for correct field assignment and default values.
        
        Verifies that creating a DeviceAccessRequest using the factory method sets the provided card_id, door_id, device_id, and pin, and automatically assigns non-null timestamp and message_id, with location_data defaulting to None.
        """
        request = DeviceAccessRequest.create(
            card_id="XYZ789",
            door_id=SAMPLE_DOOR_UUID,
            device_id="door_lock_002",
            pin="5678"
        )
        
        assert request.card_id == "XYZ789"
        assert request.door_id == SAMPLE_DOOR_UUID
        assert request.device_id == "door_lock_002"
        assert request.pin == "5678"
        assert request.timestamp is not None
        assert request.message_id is not None
        assert request.location_data is None
    
    def test_device_access_request_without_pin(self):
        """
        Tests creation of a DeviceAccessRequest without a PIN, verifying that the pin attribute is None.
        """
        request = DeviceAccessRequest.create(
            card_id="DEF456",
            door_id=SAMPLE_DOOR_UUID,
            device_id="door_lock_003"
        )
        
        assert request.card_id == "DEF456"
        assert request.door_id == SAMPLE_DOOR_UUID
        assert request.device_id == "door_lock_003"
        assert request.pin is None


class TestDeviceAccessResponse:
    """Tests for DeviceAccessResponse entity."""
    
    def test_device_access_response_granted_factory(self):
        """
        Verifies that the `create_granted` factory method of `DeviceAccessResponse` produces a response with correct granted access fields, including reason, duration, user name, card type, and default values for required attributes.
        """
        response = DeviceAccessResponse.create_granted(
            reason="Access granted for John Doe",
            duration=10,
            user_name="John Doe",
            card_type="employee"
        )
        
        assert response.access_granted is True
        assert response.door_action == DoorAction.UNLOCK
        assert response.reason == "Access granted for John Doe"
        assert response.duration == 10
        assert response.user_name == "John Doe"
        assert response.card_type == "employee"
        assert response.requires_pin is False
        assert response.message_id is not None
        assert response.timestamp is not None
    
    def test_device_access_response_denied_factory(self):
        """Test factory method for denied access response."""
        response = DeviceAccessResponse.create_denied(
            reason="Card not found",
            requires_pin=False
        )
        
        assert response.access_granted is False
        assert response.door_action == DoorAction.DENY
        assert response.reason == "Card not found"
        assert response.duration == 0
        assert response.user_name is None
        assert response.card_type is None
        assert response.requires_pin is False
        assert response.message_id is not None
        assert response.timestamp is not None
    
    def test_device_access_response_denied_with_pin_required(self):
        """
        Tests that a denied DeviceAccessResponse correctly indicates a PIN is required.
        
        Verifies that the response sets access_granted to False, door_action to REQUIRE_PIN, and requires_pin to True when a PIN is required for access denial.
        """
        response = DeviceAccessResponse.create_denied(
            reason="PIN required for high-security door",
            requires_pin=True
        )
        
        assert response.access_granted is False
        assert response.door_action == DoorAction.REQUIRE_PIN
        assert response.reason == "PIN required for high-security door"
        assert response.requires_pin is True


class TestDoorCommand:
    """Tests for DoorCommand entity."""
    
    def test_door_command_unlock_factory(self):
        """Test factory method for unlock command."""
        command = DoorCommand.create_unlock(
            device_id="door_lock_001",
            duration=5
        )
        
        assert command.command == DeviceCommandType.UNLOCK
        assert command.device_id == "door_lock_001"
        assert command.parameters["duration"] == 5
        assert command.timeout == 30
        assert command.requires_ack is True
        assert command.message_id is not None
        assert command.timestamp is not None
    
    def test_door_command_lock_factory(self):
        """Test factory method for lock command."""
        command = DoorCommand.create_lock(device_id="door_lock_002")
        
        assert command.command == DeviceCommandType.LOCK
        assert command.device_id == "door_lock_002"
        assert command.parameters == {}
        assert command.timeout == 30
        assert command.requires_ack is True
        assert command.message_id is not None
        assert command.timestamp is not None
    
    def test_door_command_status_factory(self):
        """Test factory method for status request command."""
        command = DoorCommand.create_status_request(device_id="door_lock_003")
        
        assert command.command == DeviceCommandType.STATUS
        assert command.device_id == "door_lock_003"
        assert command.parameters == {}
        assert command.requires_ack is True
        assert command.message_id is not None
        assert command.timestamp is not None


class TestDeviceStatus:
    """Tests for DeviceStatus entity."""
    
    def test_device_status_creation(self):
        """
        Verifies that a DeviceStatus instance is created with the correct attribute values.
        """
        last_heartbeat = datetime.now(timezone.utc)
        
        status = DeviceStatus(
            device_id="door_lock_001",
            online=True,
            door_state="locked",
            battery_level=85,
            signal_strength=-45,
            last_heartbeat=last_heartbeat,
            error_message=None,
            firmware_version="1.2.3"
        )
        
        assert status.device_id == "door_lock_001"
        assert status.online is True
        assert status.door_state == "locked"
        assert status.battery_level == 85
        assert status.signal_strength == -45
        assert status.last_heartbeat == last_heartbeat
        assert status.error_message is None
        assert status.firmware_version == "1.2.3"
    
    def test_device_status_is_healthy_when_online_good_battery(self):
        """Test device is healthy when online with good battery."""
        status = DeviceStatus(
            device_id="door_lock_001",
            online=True,
            door_state="locked",
            battery_level=50,
            signal_strength=-45,
            error_message=None
        )
        
        assert status.is_healthy() is True
    
    def test_device_status_unhealthy_when_offline(self):
        """
        Verifies that a device is considered unhealthy when it is offline.
        """
        status = DeviceStatus(
            device_id="door_lock_001",
            online=False,
            door_state="unknown",
            battery_level=85
        )
        
        assert status.is_healthy() is False
    
    def test_device_status_unhealthy_with_low_battery(self):
        """
        Tests that a device is considered unhealthy when its battery level is below the 20% threshold.
        """
        status = DeviceStatus(
            device_id="door_lock_001",
            online=True,
            door_state="locked",
            battery_level=15  # Below 20% threshold
        )
        
        assert status.is_healthy() is False
    
    def test_device_status_unhealthy_with_error(self):
        """
        Tests that a device with an error message is considered unhealthy.
        """
        status = DeviceStatus(
            device_id="door_lock_001",
            online=True,
            door_state="error",
            battery_level=85,
            error_message="Hardware malfunction"
        )
        
        assert status.is_healthy() is False


class TestDeviceEvent:
    """Tests for DeviceEvent entity."""
    
    def test_device_event_creation(self):
        """
        Verifies that a DeviceEvent instance is created with the correct attributes.
        """
        timestamp = datetime.now(timezone.utc)
        message_id = str(uuid4())
        
        event = DeviceEvent(
            device_id="door_lock_001",
            event_type="door_opened",
            timestamp=timestamp,
            message_id=message_id,
            details={"method": "card_swipe", "card_id": "ABC123"},
            severity="info"
        )
        
        assert event.device_id == "door_lock_001"
        assert event.event_type == "door_opened"
        assert event.timestamp == timestamp
        assert event.message_id == message_id
        assert event.details["method"] == "card_swipe"
        assert event.details["card_id"] == "ABC123"
        assert event.severity == "info"
    
    def test_device_event_door_opened_factory(self):
        """
        Tests the DeviceEvent.create_door_opened factory method for correct event creation.
        
        Verifies that the event is initialized with the provided device_id and card_id, sets the event_type to "door_opened", severity to "info", and assigns non-null timestamp and message_id.
        """
        event = DeviceEvent.create_door_opened(
            device_id="door_lock_001",
            card_id="ABC123"
        )
        
        assert event.device_id == "door_lock_001"
        assert event.event_type == "door_opened"
        assert event.details["card_id"] == "ABC123"
        assert event.severity == "info"
        assert event.timestamp is not None
        assert event.message_id is not None
    
    def test_device_event_door_opened_without_card(self):
        """Test door opened event without card."""
        event = DeviceEvent.create_door_opened(device_id="door_lock_001")
        
        assert event.device_id == "door_lock_001"
        assert event.event_type == "door_opened"
        assert event.details == {}
        assert event.severity == "info"
    
    def test_device_event_door_forced_factory(self):
        """
        Tests the factory method for creating a door forced event.
        
        Verifies that the created DeviceEvent has the correct device ID, event type, empty details, critical severity, and assigned timestamp and message ID.
        """
        event = DeviceEvent.create_door_forced(device_id="door_lock_001")
        
        assert event.device_id == "door_lock_001"
        assert event.event_type == "door_forced"
        assert event.details == {}
        assert event.severity == "critical"
        assert event.timestamp is not None
        assert event.message_id is not None
    
    def test_device_event_tamper_alert_factory(self):
        """
        Tests the DeviceEvent.create_tamper_alert factory method for generating a tamper alert event.
        
        Verifies that the event is created with the correct device ID, event type, details, severity, and that timestamp and message ID are assigned.
        """
        tamper_details = {
            "sensor": "accelerometer",
            "threshold_exceeded": True,
            "vibration_level": 8.5
        }
        
        event = DeviceEvent.create_tamper_alert(
            device_id="door_lock_001",
            details=tamper_details
        )
        
        assert event.device_id == "door_lock_001"
        assert event.event_type == "tamper_alert"
        assert event.details == tamper_details
        assert event.severity == "critical"
        assert event.timestamp is not None
        assert event.message_id is not None


class TestCommandAcknowledgment:
    """Tests for CommandAcknowledgment entity."""
    
    def test_command_acknowledgment_creation(self):
        """
        Verifies that a CommandAcknowledgment instance is created with the correct field values.
        """
        timestamp = datetime.now(timezone.utc)
        message_id = str(uuid4())
        
        ack = CommandAcknowledgment(
            message_id=message_id,
            device_id="door_lock_001",
            status="success",
            result={"door_state": "unlocked"},
            error_message=None,
            execution_time=0.25,
            timestamp=timestamp
        )
        
        assert ack.message_id == message_id
        assert ack.device_id == "door_lock_001"
        assert ack.status == "success"
        assert ack.result["door_state"] == "unlocked"
        assert ack.error_message is None
        assert ack.execution_time == 0.25
        assert ack.timestamp == timestamp
    
    def test_command_acknowledgment_auto_timestamp(self):
        """
        Tests that a CommandAcknowledgment instance automatically assigns a timestamp if not provided.
        """
        ack = CommandAcknowledgment(
            message_id=str(uuid4()),
            device_id="door_lock_001",
            status="success"
        )
        
        assert ack.timestamp is not None
        assert isinstance(ack.timestamp, datetime)
    
    def test_command_acknowledgment_is_successful_true(self):
        """
        Tests that the is_successful() method of CommandAcknowledgment returns True when the status is "success".
        """
        ack = CommandAcknowledgment(
            message_id=str(uuid4()),
            device_id="door_lock_001",
            status="success"
        )
        
        assert ack.is_successful() is True
    
    def test_command_acknowledgment_is_successful_false(self):
        """
        Tests that the is_successful() method of CommandAcknowledgment returns False for non-success statuses.
        """
        statuses = ["failed", "timeout", "invalid", "error"]
        
        for status in statuses:
            ack = CommandAcknowledgment(
                message_id=str(uuid4()),
                device_id="door_lock_001",
                status=status
            )
            
            assert ack.is_successful() is False, f"Status '{status}' should not be successful"
    
    def test_command_acknowledgment_with_error(self):
        """
        Tests creation of a CommandAcknowledgment with an error message and verifies that it is marked as unsuccessful.
        """
        ack = CommandAcknowledgment(
            message_id=str(uuid4()),
            device_id="door_lock_001",
            status="failed",
            error_message="Motor malfunction - unable to unlock",
            execution_time=None
        )
        
        assert ack.status == "failed"
        assert ack.error_message == "Motor malfunction - unable to unlock"
        assert ack.execution_time is None
        assert ack.is_successful() is False