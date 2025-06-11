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
    """Mock device communication service."""
    service = Mock(spec=DeviceCommunicationService)
    service.parse_device_request = Mock()
    service.parse_command_acknowledgment = Mock()
    service.parse_device_status = Mock()
    service.parse_device_event = Mock()
    service.broadcast_notification = AsyncMock()
    return service


@pytest.fixture
def mock_access_use_case():
    """Mock access validation use case."""
    use_case = AsyncMock(spec=ValidateAccessUseCase)
    return use_case


@pytest.fixture
def mock_mqtt_service():
    """Mock MQTT message service."""
    service = AsyncMock(spec=MqttMessageService)
    service.process_message = AsyncMock()
    return service


@pytest.fixture
def device_handler(mock_device_service, mock_access_use_case, mock_mqtt_service):
    """MQTT device handler with mocked dependencies."""
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
        """Test handling valid access request."""
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
            user_id=1
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
        """Test handling access request when parsing fails."""
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
        """Test handling access request when validation fails."""
        topic = "access/requests/door_lock_001"
        payload = json.dumps({"card_id": "ABC123", "door_id": str(TEST_DOOR_ID_1)})
        
        # Mock successful parsing
        device_request = DeviceAccessRequest.create("ABC123", 1, "door_lock_001")
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
        """Test handling command acknowledgment."""
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
        """Test handling failed command acknowledgment."""
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
        """Test handling healthy device status."""
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
        """Test handling unhealthy device status."""
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
        """Test handling info-level device event."""
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
        """Test handling critical door forced event."""
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
        """Test handling critical tamper event."""
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
        """Test handling message with invalid topic structure."""
        topic = "invalid"
        payload = "test payload"
        
        await device_handler.handle_message(topic, payload)
        
        # Should only log the general message
        mock_mqtt_service.process_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_non_access_topic(self, device_handler, mock_mqtt_service):
        """Test handling message with non-access topic."""
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
        """Test routing of access request topic."""
        topic = "access/requests/door_lock_001"
        payload = json.dumps({"card_id": "ABC123", "door_id": str(TEST_DOOR_ID_1)})
        
        mock_device_service.parse_device_request.return_value = None  # Parsing fails
        
        await device_handler.handle_message(topic, payload)
        
        mock_device_service.parse_device_request.assert_called_once_with(topic, payload)
    
    @pytest.mark.asyncio
    async def test_route_command_ack_topic(self, device_handler, mock_device_service):
        """Test routing of command acknowledgment topic."""
        topic = "access/commands/door_lock_001/ack"
        payload = json.dumps({"message_id": str(uuid4()), "status": "success"})
        
        mock_device_service.parse_command_acknowledgment.return_value = None
        
        await device_handler.handle_message(topic, payload)
        
        mock_device_service.parse_command_acknowledgment.assert_called_once_with(topic, payload)
    
    @pytest.mark.asyncio
    async def test_route_device_status_topic(self, device_handler, mock_device_service):
        """Test routing of device status topic."""
        topic = "access/devices/door_lock_001/status"
        payload = json.dumps({"online": True, "door_state": "locked"})
        
        mock_device_service.parse_device_status.return_value = None
        
        await device_handler.handle_message(topic, payload)
        
        mock_device_service.parse_device_status.assert_called_once_with(topic, payload)
    
    @pytest.mark.asyncio
    async def test_route_device_event_topic_with_type(self, device_handler, mock_device_service):
        """Test routing of device event topic with type."""
        topic = "access/events/door_opened/door_lock_001"
        payload = json.dumps({"severity": "info"})
        
        mock_device_service.parse_device_event.return_value = None
        
        await device_handler.handle_message(topic, payload)
        
        mock_device_service.parse_device_event.assert_called_once_with(topic, payload)
    
    @pytest.mark.asyncio
    async def test_route_device_event_topic_without_type(self, device_handler, mock_device_service):
        """Test routing of device event topic without type."""
        topic = "access/events/door_lock_001"
        payload = json.dumps({"event_type": "door_opened", "severity": "info"})
        
        mock_device_service.parse_device_event.return_value = None
        
        await device_handler.handle_message(topic, payload)
        
        mock_device_service.parse_device_event.assert_called_once_with(topic, payload)
    
    @pytest.mark.asyncio
    async def test_ignore_incomplete_access_topics(self, device_handler, mock_device_service):
        """Test that incomplete access topics are ignored."""
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
        """Test message logging failure handling."""
        topic = "test/topic"
        payload = "test payload"
        
        mock_mqtt_service.process_message.side_effect = Exception("Database error")
        
        # Should not raise exception
        await device_handler._log_message(topic, payload)
        
        mock_mqtt_service.process_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_command_acknowledgment(self, device_handler, mock_mqtt_service):
        """Test logging command acknowledgment."""
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
        """Test logging device event."""
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