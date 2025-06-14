"""
Tests for MQTT device handler.
"""
import pytest
import json
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timezone
from uuid import uuid4, UUID

# Test UUIDs for consistent test data
TEST_DOOR_ID_1 = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d483")

from tests.conftest import SAMPLE_CARD_UUID, SAMPLE_DOOR_UUID

from app.domain.services.mqtt_device_handler import MqttDeviceHandler
from app.domain.services.device_communication_service import DeviceCommunicationService
from app.application.use_cases.access_use_cases import ValidateAccessUseCase
from app.domain.services.mqtt_message_service import MqttMessageService
from app.api.schemas.access_schemas import AccessValidationResult
from app.domain.entities.device_message import (
    DeviceAccessRequest,
    DeviceStatus,
    DeviceEvent,
    CommandAcknowledgment
)


@pytest.fixture
def mock_device_service():
    """
    Creates a mock instance of the device communication service with mocked parsing and notification methods for testing purposes.
    
    Returns:
        A mock DeviceCommunicationService with all parsing methods and broadcast_notification mocked.
    """
    service = Mock(spec=DeviceCommunicationService)
    service.parse_device_request = Mock()
    service.parse_command_acknowledgment = Mock()
    service.parse_device_status = Mock()
    service.parse_device_event = Mock()
    service.broadcast_notification = AsyncMock()
    return service


@pytest.fixture
def mock_access_use_case():
    """
    Creates an asynchronous mock instance of the access validation use case for testing.
    """
    use_case = AsyncMock(spec=ValidateAccessUseCase)
    return use_case


@pytest.fixture
def mock_mqtt_service():
    """
    Creates a mock instance of the MQTT message service for testing.
    
    Returns:
        An asynchronous mock of MqttMessageService with a mocked process_message method.
    """
    service = AsyncMock(spec=MqttMessageService)
    service.process_message = AsyncMock()
    return service


@pytest.fixture
def device_handler(mock_device_service, mock_access_use_case, mock_mqtt_service):
    """
    Creates an instance of MqttDeviceHandler with mocked service dependencies for testing.
    
    Returns:
        An MqttDeviceHandler configured with the provided mock services.
    """
    return MqttDeviceHandler(
        device_communication_service=mock_device_service,
        access_validation_use_case=mock_access_use_case,
        mqtt_message_service=mock_mqtt_service
    )


class TestMqttDeviceHandler:
    """Tests for MqttDeviceHandler message routing."""
    
    @pytest.mark.asyncio
    async def test_handle_message_logs_all_messages(self, device_handler, mock_mqtt_service):
        """Test that all incoming messages are logged."""
        topic = "test/topic"
        payload = "test payload"
        
        await device_handler.handle_message(topic, payload)
        
        mock_mqtt_service.process_message.assert_called_once()
        logged_message = mock_mqtt_service.process_message.call_args[0][0]
        assert logged_message.topic == topic
        assert logged_message.message == payload
    
    @pytest.mark.asyncio
    async def test_handle_access_request_valid_topic(self, device_handler, mock_device_service, mock_access_use_case):
        """
        Tests that a valid access request message is correctly parsed and triggers access validation.
        
        Verifies that the device request is parsed from the topic and payload, and that the access validation use case is executed with the expected parameters.
        """
        topic = "access/requests/door_lock_001"
        payload = json.dumps({
            "card_id": "ABC123",
            "door_id": str(TEST_DOOR_ID_1),
            "pin": "1234"
        })
        
        # Mock device request parsing
        device_request = DeviceAccessRequest(
            card_id="ABC123",
            door_id=TEST_DOOR_ID_1,
            device_id="door_lock_001",
            pin="1234",
            timestamp=datetime.now(timezone.utc),
            message_id=str(uuid4())
        )
        mock_device_service.parse_device_request.return_value = device_request
        
        # Mock access validation result
        mock_access_use_case.execute.return_value = AccessValidationResult(
            access_granted=True,
            reason="Access granted",
            door_name="Main Door",
            user_name="John Doe",
            card_type="employee",
            requires_pin=False,
            card_id="ABC123",
            door_id=TEST_DOOR_ID_1,
            user_id=SAMPLE_CARD_UUID
        )
        
        await device_handler.handle_message(topic, payload)
        
        # Verify parsing was called
        mock_device_service.parse_device_request.assert_called_once_with(topic, payload)
        
        # Verify access validation was called with correct parameters
        mock_access_use_case.execute.assert_called_once_with(
            card_id="ABC123",
            door_id=TEST_DOOR_ID_1,
            pin="1234",
            device_id="door_lock_001"
        )
    
    @pytest.mark.asyncio
    async def test_handle_access_request_parsing_failure(self, device_handler, mock_device_service, mock_access_use_case):
        """
        Tests that when parsing an access request fails, validation is not attempted.
        
        Simulates a parsing failure for an access request topic and verifies that the access validation use case is not called.
        """
        topic = "access/requests/door_lock_001"
        payload = "invalid json"
        
        # Mock parsing failure
        mock_device_service.parse_device_request.return_value = None
        
        await device_handler.handle_message(topic, payload)
        
        # Verify parsing was called but validation was not
        mock_device_service.parse_device_request.assert_called_once_with(topic, payload)
        mock_access_use_case.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_access_request_validation_failure(self, device_handler, mock_device_service, mock_access_use_case):
        """
        Tests that when access validation fails during handling of an access request, the exception is caught and does not propagate, while both parsing and validation methods are called.
        """
        topic = "access/requests/door_lock_001"
        payload = json.dumps({"card_id": "ABC123", "door_id": str(TEST_DOOR_ID_1)})
        
        # Mock successful parsing
        device_request = DeviceAccessRequest.create("ABC123", TEST_DOOR_ID_1, "door_lock_001")
        mock_device_service.parse_device_request.return_value = device_request
        
        # Mock validation failure
        mock_access_use_case.execute.side_effect = Exception("Card not found")
        
        # Should not raise exception
        await device_handler.handle_message(topic, payload)
        
        # Verify both parsing and validation were called
        mock_device_service.parse_device_request.assert_called_once()
        mock_access_use_case.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_command_acknowledgment(self, device_handler, mock_device_service, mock_mqtt_service):
        """
        Verifies that command acknowledgment messages are correctly parsed and logged.
        
        This test ensures that when a command acknowledgment message is received, the handler parses the acknowledgment and logs both the general message and the acknowledgment audit entry.
        """
        topic = "access/commands/door_lock_001/ack"
        payload = json.dumps({
            "message_id": str(uuid4()),
            "status": "success",
            "execution_time": 0.5
        })
        
        # Mock acknowledgment parsing
        ack = CommandAcknowledgment(
            message_id=str(uuid4()),
            device_id="door_lock_001",
            status="success",
            execution_time=0.5
        )
        mock_device_service.parse_command_acknowledgment.return_value = ack
        
        await device_handler.handle_message(topic, payload)
        
        mock_device_service.parse_command_acknowledgment.assert_called_once_with(topic, payload)
        
        # Verify audit logging was called (once for general message, once for ack)
        assert mock_mqtt_service.process_message.call_count == 2
    
    @pytest.mark.asyncio
    async def test_handle_command_acknowledgment_failed_command(self, device_handler, mock_device_service, mock_mqtt_service):
        """
        Tests that a failed command acknowledgment is handled by logging both the acknowledgment and an additional alert message.
        """
        topic = "access/commands/door_lock_001/ack"
        payload = json.dumps({
            "message_id": str(uuid4()),
            "status": "failed",
            "error_message": "Motor malfunction"
        })
        
        # Mock failed acknowledgment
        ack = CommandAcknowledgment(
            message_id=str(uuid4()),
            device_id="door_lock_001",
            status="failed",
            error_message="Motor malfunction"
        )
        mock_device_service.parse_command_acknowledgment.return_value = ack
        
        await device_handler.handle_message(topic, payload)
        
        # Verify additional alert logging for failed command
        assert mock_mqtt_service.process_message.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_handle_device_status_healthy(self, device_handler, mock_device_service, mock_mqtt_service):
        """
        Tests that a healthy device status message is handled correctly.
        
        Verifies that the device status is parsed, no alerts are triggered, and both the general message and device status are logged.
        """
        topic = "access/devices/door_lock_001/status"
        payload = json.dumps({
            "online": True,
            "door_state": "locked",
            "battery_level": 85
        })
        
        # Mock healthy status
        status = DeviceStatus(
            device_id="door_lock_001",
            online=True,
            door_state="locked",
            battery_level=85
        )
        mock_device_service.parse_device_status.return_value = status
        
        await device_handler.handle_message(topic, payload)
        
        mock_device_service.parse_device_status.assert_called_once_with(topic, payload)
        
        # Should log general message and status (no alert for healthy device)
        assert mock_mqtt_service.process_message.call_count == 2
    
    @pytest.mark.asyncio
    async def test_handle_device_status_unhealthy(self, device_handler, mock_device_service, mock_mqtt_service):
        """
        Tests that the handler processes an unhealthy device status message by logging the general message, device status, and a health alert when the device reports an error state and low battery.
        """
        topic = "access/devices/door_lock_001/status"
        payload = json.dumps({
            "online": True,
            "door_state": "error",
            "battery_level": 15,  # Low battery
            "error_message": "Motor malfunction"
        })
        
        # Mock unhealthy status
        status = DeviceStatus(
            device_id="door_lock_001",
            online=True,
            door_state="error",
            battery_level=15,
            error_message="Motor malfunction"
        )
        mock_device_service.parse_device_status.return_value = status
        
        await device_handler.handle_message(topic, payload)
        
        # Should log general message, status, and health alert
        assert mock_mqtt_service.process_message.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_handle_device_event_info_level(self, device_handler, mock_device_service, mock_mqtt_service):
        """
        Tests that an info-level device event is handled by parsing the event and logging both the general message and the event, without triggering critical handling.
        """
        topic = "access/events/door_opened/door_lock_001"
        payload = json.dumps({
            "details": {"card_id": "ABC123"},
            "severity": "info"
        })
        
        # Mock info event
        event = DeviceEvent.create_door_opened("door_lock_001", "ABC123")
        mock_device_service.parse_device_event.return_value = event
        
        await device_handler.handle_message(topic, payload)
        
        mock_device_service.parse_device_event.assert_called_once_with(topic, payload)
        
        # Should log general message and event (no critical handling)
        assert mock_mqtt_service.process_message.call_count == 2
    
    @pytest.mark.asyncio
    async def test_handle_device_event_critical_door_forced(self, device_handler, mock_device_service, mock_mqtt_service):
        """
        Tests that a critical 'door forced' device event is handled by logging messages and broadcasting a critical security notification.
        
        Verifies that the event is parsed, appropriate messages are logged, and a broadcast notification is sent with the correct alert content and severity.
        """
        topic = "access/events/door_forced/door_lock_001"
        payload = json.dumps({
            "severity": "critical",
            "details": {}
        })
        
        # Mock critical event
        event = DeviceEvent.create_door_forced("door_lock_001")
        mock_device_service.parse_device_event.return_value = event
        
        await device_handler.handle_message(topic, payload)
        
        # Should log general message, event, critical alert, and broadcast notification
        assert mock_mqtt_service.process_message.call_count >= 2
        mock_device_service.broadcast_notification.assert_called_once()
        
        # Verify broadcast content
        call_args = mock_device_service.broadcast_notification.call_args
        assert "SECURITY ALERT" in call_args[0][0]
        assert "door forced open" in call_args[0][0].lower()
        assert call_args[1]["severity"] == "critical"
    
    @pytest.mark.asyncio
    async def test_handle_device_event_critical_tamper(self, device_handler, mock_device_service, mock_mqtt_service):
        """
        Tests that a critical tamper alert event is handled by broadcasting a security alert notification.
        
        Verifies that when a critical tamper event message is received, the handler parses the event, triggers a broadcast notification with the correct alert content, and includes the expected severity level.
        """
        topic = "access/events/tamper_alert/door_lock_001"
        payload = json.dumps({
            "severity": "critical",
            "details": {"sensor": "accelerometer"}
        })
        
        # Mock tamper event
        event = DeviceEvent.create_tamper_alert("door_lock_001", {"sensor": "accelerometer"})
        mock_device_service.parse_device_event.return_value = event
        
        await device_handler.handle_message(topic, payload)
        
        # Should handle critical event and broadcast alert
        mock_device_service.broadcast_notification.assert_called_once()
        
        # Verify broadcast content
        call_args = mock_device_service.broadcast_notification.call_args
        assert "SECURITY ALERT" in call_args[0][0]
        assert "tamper detected" in call_args[0][0].lower()
        assert call_args[1]["severity"] == "critical"
    
    @pytest.mark.asyncio
    async def test_handle_invalid_topic_structure(self, device_handler, mock_mqtt_service):
        """
        Tests that messages with an invalid topic structure are only logged and not further processed.
        """
        topic = "invalid"
        payload = "test payload"
        
        await device_handler.handle_message(topic, payload)
        
        # Should only log the general message
        mock_mqtt_service.process_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_non_access_topic(self, device_handler, mock_mqtt_service):
        """
        Tests that messages with non-access topics are only logged and not further processed.
        """
        topic = "system/health/check"
        payload = "test payload"
        
        await device_handler.handle_message(topic, payload)
        
        # Should only log the general message
        mock_mqtt_service.process_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_message_exception_handling(self, device_handler, mock_mqtt_service):
        """Test exception handling in message processing."""
        topic = "access/requests/door_lock_001"
        payload = "test payload"
        
        # Make logging fail to test exception handling
        mock_mqtt_service.process_message.side_effect = Exception("Database error")
        
        # Should not raise exception
        await device_handler.handle_message(topic, payload)
        
        # Exception should be caught and logged
        mock_mqtt_service.process_message.assert_called_once()


class TestTopicRouting:
    """Tests for topic routing logic."""
    
    @pytest.mark.asyncio
    async def test_route_access_request_topic(self, device_handler, mock_device_service):
        """
        Tests that access request topics are routed to the device request parser.
        
        Verifies that when an access request topic is received, the `parse_device_request` method is called with the correct topic and payload, even if parsing fails.
        """
        topic = "access/requests/door_lock_001"
        payload = json.dumps({"card_id": "ABC123", "door_id": str(TEST_DOOR_ID_1)})
        
        mock_device_service.parse_device_request.return_value = None  # Parsing fails
        
        await device_handler.handle_message(topic, payload)
        
        mock_device_service.parse_device_request.assert_called_once_with(topic, payload)
    
    @pytest.mark.asyncio
    async def test_route_command_ack_topic(self, device_handler, mock_device_service):
        """
        Tests that command acknowledgment topics are routed to the command acknowledgment parser.
        
        Verifies that when a message with a command acknowledgment topic is received, the device handler calls `parse_command_acknowledgment` with the correct topic and payload.
        """
        topic = "access/commands/door_lock_001/ack"
        payload = json.dumps({"message_id": str(uuid4()), "status": "success"})
        
        mock_device_service.parse_command_acknowledgment.return_value = None
        
        await device_handler.handle_message(topic, payload)
        
        mock_device_service.parse_command_acknowledgment.assert_called_once_with(topic, payload)
    
    @pytest.mark.asyncio
    async def test_route_device_status_topic(self, device_handler, mock_device_service):
        """
        Tests that device status topics are correctly routed to the device status parser.
        
        Verifies that when a device status message is received, the `parse_device_status` method of the device service is called with the appropriate topic and payload.
        """
        topic = "access/devices/door_lock_001/status"
        payload = json.dumps({"online": True, "door_state": "locked"})
        
        mock_device_service.parse_device_status.return_value = None
        
        await device_handler.handle_message(topic, payload)
        
        mock_device_service.parse_device_status.assert_called_once_with(topic, payload)
    
    @pytest.mark.asyncio
    async def test_route_device_event_topic_with_type(self, device_handler, mock_device_service):
        """
        Tests that device event topics containing an explicit event type are routed to the device event parser.
        
        Verifies that when a topic includes an event type, the `parse_device_event` method is called with the correct arguments.
        """
        topic = "access/events/door_opened/door_lock_001"
        payload = json.dumps({"severity": "info"})
        
        mock_device_service.parse_device_event.return_value = None
        
        await device_handler.handle_message(topic, payload)
        
        mock_device_service.parse_device_event.assert_called_once_with(topic, payload)
    
    @pytest.mark.asyncio
    async def test_route_device_event_topic_without_type(self, device_handler, mock_device_service):
        """
        Tests that device event topics without an explicit event type in the topic are routed to the device event parser.
        """
        topic = "access/events/door_lock_001"
        payload = json.dumps({"event_type": "door_opened", "severity": "info"})
        
        mock_device_service.parse_device_event.return_value = None
        
        await device_handler.handle_message(topic, payload)
        
        mock_device_service.parse_device_event.assert_called_once_with(topic, payload)
    
    @pytest.mark.asyncio
    async def test_ignore_incomplete_access_topics(self, device_handler, mock_device_service):
        """
        Verifies that messages with incomplete or malformed access-related topics are ignored and do not trigger any parsing methods.
        """
        incomplete_topics = [
            "access",
            "access/requests",
            "access/commands/door_lock_001",  # Missing /ack
            "access/devices/door_lock_001"    # Missing /status
        ]
        
        for topic in incomplete_topics:
            await device_handler.handle_message(topic, "test payload")
        
        # None of the parsing methods should be called
        mock_device_service.parse_device_request.assert_not_called()
        mock_device_service.parse_command_acknowledgment.assert_not_called()
        mock_device_service.parse_device_status.assert_not_called()
        mock_device_service.parse_device_event.assert_not_called()


class TestLoggingFunctionality:
    """Tests for audit logging functionality."""
    
    @pytest.mark.asyncio
    async def test_log_message_success(self, device_handler, mock_mqtt_service):
        """Test successful message logging."""
        topic = "test/topic"
        payload = "test payload"
        
        await device_handler._log_message(topic, payload)
        
        mock_mqtt_service.process_message.assert_called_once()
        logged_message = mock_mqtt_service.process_message.call_args[0][0]
        assert logged_message.topic == topic
        assert logged_message.message == payload
        assert isinstance(logged_message.timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_log_message_failure(self, device_handler, mock_mqtt_service):
        """
        Tests that message logging failures in _log_message are handled without raising exceptions.
        """
        topic = "test/topic"
        payload = "test payload"
        
        mock_mqtt_service.process_message.side_effect = Exception("Database error")
        
        # Should not raise exception
        await device_handler._log_message(topic, payload)
        
        mock_mqtt_service.process_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_command_acknowledgment(self, device_handler, mock_mqtt_service):
        """
        Tests that command acknowledgment logging creates an audit message with the correct topic and content.
        
        Verifies that the `_log_command_acknowledgment` method logs a message to the expected audit topic with JSON data reflecting the acknowledgment details.
        """
        ack = CommandAcknowledgment(
            message_id=str(uuid4()),
            device_id="door_lock_001",
            status="success",
            execution_time=0.5
        )
        
        await device_handler._log_command_acknowledgment(ack)
        
        mock_mqtt_service.process_message.assert_called_once()
        logged_message = mock_mqtt_service.process_message.call_args[0][0]
        assert logged_message.topic == f"audit/commands/{ack.device_id}/ack"
        
        # Verify logged data
        logged_data = json.loads(logged_message.message)
        assert logged_data["event_type"] == "command_acknowledgment"
        assert logged_data["device_id"] == ack.device_id
        assert logged_data["message_id"] == ack.message_id
        assert logged_data["status"] == ack.status
        assert logged_data["execution_time"] == ack.execution_time
    
    @pytest.mark.asyncio
    async def test_log_device_status(self, device_handler, mock_mqtt_service):
        """Test logging device status."""
        status = DeviceStatus(
            device_id="door_lock_001",
            online=True,
            door_state="locked",
            battery_level=75
        )
        
        await device_handler._log_device_status(status)
        
        mock_mqtt_service.process_message.assert_called_once()
        logged_message = mock_mqtt_service.process_message.call_args[0][0]
        assert logged_message.topic == f"monitoring/devices/{status.device_id}/status"
        
        logged_data = json.loads(logged_message.message)
        assert logged_data["event_type"] == "device_status"
        assert logged_data["device_id"] == status.device_id
        assert logged_data["online"] == status.online
        assert logged_data["door_state"] == status.door_state
        assert logged_data["battery_level"] == status.battery_level
        assert logged_data["is_healthy"] == status.is_healthy()
    
    @pytest.mark.asyncio
    async def test_log_device_event(self, device_handler, mock_mqtt_service):
        """
        Verifies that device events are logged with the correct topic and message content.
        
        Ensures that the `_log_device_event` method logs a device event to the expected audit topic, and that the logged message contains accurate event details.
        """
        event = DeviceEvent.create_door_opened("door_lock_001", "ABC123")
        
        await device_handler._log_device_event(event)
        
        mock_mqtt_service.process_message.assert_called_once()
        logged_message = mock_mqtt_service.process_message.call_args[0][0]
        assert logged_message.topic == f"audit/events/{event.device_id}/{event.event_type}"
        
        logged_data = json.loads(logged_message.message)
        assert logged_data["event_type"] == event.event_type
        assert logged_data["device_id"] == event.device_id
        assert logged_data["severity"] == event.severity
        assert logged_data["details"] == event.details
        assert logged_data["message_id"] == event.message_id