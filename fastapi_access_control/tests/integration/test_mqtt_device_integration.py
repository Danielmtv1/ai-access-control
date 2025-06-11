"""
Integration tests for MQTT device bidirectional communication.
"""
import pytest
import json
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone
from uuid import uuid4, UUID

from app.domain.services.mqtt_device_handler import MqttDeviceHandler
from app.domain.services.device_communication_service import DeviceCommunicationService
from app.application.use_cases.access_use_cases import ValidateAccessUseCase
from app.domain.services.mqtt_message_service import MqttMessageService
from app.api.schemas.access_schemas import AccessValidationResult
from app.domain.entities.device_message import (
    DeviceAccessRequest,
    DeviceAccessResponse,
    DoorCommand,
    DeviceStatus,
    DeviceEvent,
    CommandAcknowledgment,
    DoorAction
)
from app.domain.entities.card import Card, CardType, CardStatus
from app.domain.entities.door import Door, DoorStatus, SecurityLevel, DoorType
from app.domain.entities.user import User, UserStatus, Role
from app.domain.entities.permission import Permission, PermissionStatus


@pytest.fixture
def mock_mqtt_adapter():
    """Mock MQTT adapter for integration testing."""
    adapter = AsyncMock()
    adapter.publish = AsyncMock()
    return adapter


@pytest.fixture
def mock_repositories():
    """Mock repositories for testing."""
    card_repo = AsyncMock()
    door_repo = AsyncMock()
    user_repo = AsyncMock()
    permission_repo = AsyncMock()
    mqtt_service = AsyncMock()
    
    return {
        'card_repository': card_repo,
        'door_repository': door_repo,
        'user_repository': user_repo,
        'permission_repository': permission_repo,
        'mqtt_service': mqtt_service
    }


@pytest.fixture
def sample_entities():
    """Sample entities for testing."""
    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    card_id = UUID("550e8400-e29b-41d4-a716-446655440001")
    
    user = User(
        id=user_id,
        email="john.doe@example.com",
        hashed_password="hashed_password",
        full_name="John Doe",
        roles=[Role.USER],
        status=UserStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    card = Card(
        id=card_id,
        card_id="ABC123",
        user_id=user_id,
        card_type=CardType.EMPLOYEE,
        status=CardStatus.ACTIVE,
        valid_from=datetime.now(timezone.utc),
        valid_until=None,
        use_count=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_used=None
    )
    
    door = Door(
        id=1,
        name="Main Entrance",
        location="Building A",
        door_type=DoorType.ENTRANCE,
        security_level=SecurityLevel.MEDIUM,
        status=DoorStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    permission = Permission(
        id=1,
        user_id=1,  # Use int instead of UUID for permission
        door_id=1,
        status=PermissionStatus.ACTIVE,
        created_by=1,  # Use int instead of UUID
        valid_from=datetime.now(timezone.utc),
        valid_until=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    return {
        'user': user,
        'card': card,
        'door': door,
        'permission': permission
    }


@pytest.fixture
def integrated_system(mock_mqtt_adapter, mock_repositories):
    """Fully integrated MQTT device communication system."""
    # Create device communication service
    device_service = DeviceCommunicationService(mock_mqtt_adapter)
    
    # Create access validation use case
    access_use_case = ValidateAccessUseCase(
        card_repository=mock_repositories['card_repository'],
        door_repository=mock_repositories['door_repository'],
        permission_repository=mock_repositories['permission_repository'],
        user_repository=mock_repositories['user_repository'],
        mqtt_service=mock_repositories['mqtt_service'],
        device_communication_service=device_service
    )
    
    # Create MQTT device handler
    device_handler = MqttDeviceHandler(
        device_communication_service=device_service,
        access_validation_use_case=access_use_case,
        mqtt_message_service=mock_repositories['mqtt_service']
    )
    
    return {
        'device_service': device_service,
        'access_use_case': access_use_case,
        'device_handler': device_handler,
        'mqtt_adapter': mock_mqtt_adapter,
        'repositories': mock_repositories
    }


class TestMqttDeviceIntegration:
    """Integration tests for complete MQTT device communication flow."""
    TEST_DOOR_ID = UUID("550e8400-e29b-41d4-a716-446655440002")
    @pytest.mark.asyncio
    async def test_complete_access_granted_flow(self, integrated_system, sample_entities):
        """Test complete flow from device request to unlock command."""
        system = integrated_system
        entities = sample_entities
        
        # Setup repository mocks
        system['repositories']['card_repository'].get_by_card_id.return_value = entities['card']
        system['repositories']['door_repository'].get_by_id.return_value = entities['door']
        system['repositories']['user_repository'].get_by_id.return_value = entities['user']
        system['repositories']['permission_repository'].check_access.return_value = True
        system['repositories']['card_repository'].update.return_value = None
        system['repositories']['door_repository'].update.return_value = None
        
        # Simulate device access request
        topic = "access/requests/door_lock_001"
        payload = json.dumps({
            "card_id": "ABC123",
            "door_id": self.TEST_DOOR_ID,
            "pin": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_id": str(uuid4())
        })
        
        # Process the request
        await system['device_handler'].handle_message(topic, payload)
        
        # Verify access validation was called
        system['repositories']['card_repository'].get_by_card_id.assert_called_once_with("ABC123")
        system['repositories']['door_repository'].get_by_id.assert_called_once_with(1)
        system['repositories']['user_repository'].get_by_id.assert_called_once_with(1)
        system['repositories']['permission_repository'].check_access.assert_called_once()
        
        # Verify MQTT responses were published
        assert system['mqtt_adapter'].publish.call_count >= 2  # Response + unlock command
        
        # Verify access response was sent
        publish_calls = system['mqtt_adapter'].publish.call_args_list
        response_call = None
        unlock_call = None
        
        for call in publish_calls:
            topic_arg = call[0][0]
            if topic_arg == "access/responses/door_lock_001":
                response_call = call
            elif topic_arg == "access/commands/door_lock_001":
                unlock_call = call
        
        assert response_call is not None, "Access response should be published"
        assert unlock_call is not None, "Unlock command should be published"
        
        # Verify response content
        response_payload = json.loads(response_call[0][1])
        assert response_payload["access_granted"] is True
        assert response_payload["door_action"] == "unlock"
        assert response_payload["user_name"] == "John Doe"
        
        # Verify unlock command content
        unlock_payload = json.loads(unlock_call[0][1])
        assert unlock_payload["command"] == "unlock"
        assert unlock_payload["parameters"]["duration"] == 5
    
    @pytest.mark.asyncio
    async def test_complete_access_denied_flow(self, integrated_system, sample_entities):
        """Test complete flow for denied access."""
        system = integrated_system
        entities = sample_entities
        
        # Setup repository mocks for denial (no permission)
        system['repositories']['card_repository'].get_by_card_id.return_value = entities['card']
        system['repositories']['door_repository'].get_by_id.return_value = entities['door']
        system['repositories']['user_repository'].get_by_id.return_value = entities['user']
        system['repositories']['permission_repository'].check_access.return_value = False
        
        # Simulate device access request
        topic = "access/requests/door_lock_001"
        payload = json.dumps({
            "card_id": "ABC123",
            "door_id": self.TEST_DOOR_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_id": str(uuid4())
        })
        
        # Process the request
        await system['device_handler'].handle_message(topic, payload)
        
        # Verify MQTT response was published (denial response)
        publish_calls = system['mqtt_adapter'].publish.call_args_list
        response_call = None
        
        for call in publish_calls:
            topic_arg = call[0][0]
            if topic_arg == "access/responses/door_lock_001":
                response_call = call
                break
        
        assert response_call is not None, "Access denial response should be published"
        
        # Verify denial response content
        response_payload = json.loads(response_call[0][1])
        assert response_payload["access_granted"] is False
        assert response_payload["door_action"] == "deny"
        assert "does not have permission" in response_payload["reason"]
    
    @pytest.mark.asyncio
    async def test_master_card_access_flow(self, integrated_system, sample_entities):
        """Test master card access flow."""
        system = integrated_system
        entities = sample_entities
        
        # Create master card
        master_card = Card(
            id=2,
            card_id="MASTER001",
            user_id=1,
            card_type=CardType.MASTER,
            status=CardStatus.ACTIVE,
            issued_at=datetime.now(timezone.utc),
            valid_from=datetime.now(timezone.utc),
            valid_until=None,
            use_count=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Setup repository mocks
        system['repositories']['card_repository'].get_by_card_id.return_value = master_card
        system['repositories']['door_repository'].get_by_id.return_value = entities['door']
        system['repositories']['user_repository'].get_by_id.return_value = entities['user']
        system['repositories']['card_repository'].update.return_value = None
        system['repositories']['door_repository'].update.return_value = None
        
        # Simulate master card request
        topic = "access/requests/door_lock_001"
        payload = json.dumps({
            "card_id": "MASTER001",
            "door_id": self.TEST_DOOR_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_id": str(uuid4())
        })
        
        # Process the request
        await system['device_handler'].handle_message(topic, payload)
        
        # Master card should not require permission check
        system['repositories']['permission_repository'].check_access.assert_not_called()
        
        # Verify master card response
        publish_calls = system['mqtt_adapter'].publish.call_args_list
        response_call = None
        
        for call in publish_calls:
            topic_arg = call[0][0]
            if topic_arg == "access/responses/door_lock_001":
                response_call = call
                break
        
        assert response_call is not None
        response_payload = json.loads(response_call[0][1])
        assert response_payload["access_granted"] is True
        assert response_payload["card_type"] == "master"
        assert "Master card access granted" in response_payload["reason"]
    
    @pytest.mark.asyncio
    async def test_pin_required_flow(self, integrated_system, sample_entities):
        """Test PIN required flow for high-security door."""
        system = integrated_system
        entities = sample_entities
        
        # Create high-security door
        high_security_door = Door(
            id=2,
            name="Server Room",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.CRITICAL,
            status=DoorStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Setup repository mocks
        system['repositories']['card_repository'].get_by_card_id.return_value = entities['card']
        system['repositories']['door_repository'].get_by_id.return_value = high_security_door
        system['repositories']['user_repository'].get_by_id.return_value = entities['user']
        system['repositories']['permission_repository'].check_access.return_value = True
        
        # Simulate request without PIN to critical door
        topic = "access/requests/door_lock_001"
        payload = json.dumps({
            "card_id": "ABC123",
            "door_id": 2,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_id": str(uuid4())
        })
        
        # Process the request
        await system['device_handler'].handle_message(topic, payload)
        
        # Verify PIN required response
        publish_calls = system['mqtt_adapter'].publish.call_args_list
        response_call = None
        
        for call in publish_calls:
            topic_arg = call[0][0]
            if topic_arg == "access/responses/door_lock_001":
                response_call = call
                break
        
        assert response_call is not None
        response_payload = json.loads(response_call[0][1])
        assert response_payload["access_granted"] is False
        assert response_payload["door_action"] == "require_pin"
        assert response_payload["requires_pin"] is True
        assert "PIN required" in response_payload["reason"]
    
    @pytest.mark.asyncio
    async def test_command_acknowledgment_flow(self, integrated_system):
        """Test command acknowledgment processing."""
        system = integrated_system
        
        # Create and track a command
        command = DoorCommand.create_unlock("door_lock_001", duration=5)
        system['device_service']._pending_commands[command.message_id] = command
        
        # Simulate command acknowledgment
        topic = f"access/commands/door_lock_001/ack"
        payload = json.dumps({
            "message_id": command.message_id,
            "status": "success",
            "result": {"door_state": "unlocked"},
            "execution_time": 0.75,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Process the acknowledgment
        await system['device_handler'].handle_message(topic, payload)
        
        # Verify command was removed from pending
        pending = system['device_service'].get_pending_commands()
        assert command.message_id not in pending
        
        # Verify audit logging
        system['repositories']['mqtt_service'].process_message.assert_called()
    
    @pytest.mark.asyncio
    async def test_failed_command_acknowledgment_flow(self, integrated_system):
        """Test failed command acknowledgment processing."""
        system = integrated_system
        
        # Create and track a command
        command = DoorCommand.create_unlock("door_lock_001")
        system['device_service']._pending_commands[command.message_id] = command
        
        # Simulate failed command acknowledgment
        topic = f"access/commands/door_lock_001/ack"
        payload = json.dumps({
            "message_id": command.message_id,
            "status": "failed",
            "error_message": "Motor malfunction",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Process the acknowledgment
        await system['device_handler'].handle_message(topic, payload)
        
        # Verify command was still removed from pending
        pending = system['device_service'].get_pending_commands()
        assert command.message_id not in pending
        
        # Verify failure handling - should log additional alert
        assert system['repositories']['mqtt_service'].process_message.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_device_status_monitoring_flow(self, integrated_system):
        """Test device status monitoring and health alerts."""
        system = integrated_system
        
        # Simulate healthy device status
        topic = "access/devices/door_lock_001/status"
        payload = json.dumps({
            "online": True,
            "door_state": "locked",
            "battery_level": 85,
            "signal_strength": -45,
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
            "firmware_version": "1.2.3"
        })
        
        # Process healthy status
        await system['device_handler'].handle_message(topic, payload)
        
        # Should log status but no health alerts
        initial_call_count = system['repositories']['mqtt_service'].process_message.call_count
        
        # Simulate unhealthy device status (low battery)
        unhealthy_payload = json.dumps({
            "online": True,
            "door_state": "locked",
            "battery_level": 15,  # Low battery
            "signal_strength": -45,
            "error_message": "Battery low",
            "last_heartbeat": datetime.now(timezone.utc).isoformat()
        })
        
        # Process unhealthy status
        await system['device_handler'].handle_message(topic, unhealthy_payload)
        
        # Should log status and health alert
        assert system['repositories']['mqtt_service'].process_message.call_count > initial_call_count
    
    @pytest.mark.asyncio
    async def test_critical_security_event_flow(self, integrated_system):
        """Test critical security event handling."""
        system = integrated_system
        
        # Simulate door forced event
        topic = "access/events/door_forced/door_lock_001"
        payload = json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_id": str(uuid4()),
            "details": {"force_detected": True, "sensor_reading": 8.5},
            "severity": "critical"
        })
        
        # Process the critical event
        await system['device_handler'].handle_message(topic, payload)
        
        # Verify broadcast notification was sent
        system['mqtt_adapter'].publish.assert_called()
        
        # Find broadcast call
        broadcast_call = None
        for call in system['mqtt_adapter'].publish.call_args_list:
            if call[0][0] == "access/notifications/broadcast":
                broadcast_call = call
                break
        
        assert broadcast_call is not None, "Broadcast notification should be sent"
        
        broadcast_payload = json.loads(broadcast_call[0][1])
        assert "SECURITY ALERT" in broadcast_payload["message"]
        assert "door forced open" in broadcast_payload["message"].lower()
        assert broadcast_payload["severity"] == "critical"
    
    @pytest.mark.asyncio
    async def test_tamper_detection_flow(self, integrated_system):
        """Test tamper detection event handling."""
        system = integrated_system
        
        # Simulate tamper alert
        topic = "access/events/tamper_alert/door_lock_001"
        payload = json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_id": str(uuid4()),
            "details": {
                "sensor": "accelerometer",
                "threshold_exceeded": True,
                "vibration_level": 9.2
            },
            "severity": "critical"
        })
        
        # Process the tamper event
        await system['device_handler'].handle_message(topic, payload)
        
        # Verify broadcast notification was sent
        broadcast_call = None
        for call in system['mqtt_adapter'].publish.call_args_list:
            if call[0][0] == "access/notifications/broadcast":
                broadcast_call = call
                break
        
        assert broadcast_call is not None
        broadcast_payload = json.loads(broadcast_call[0][1])
        assert "SECURITY ALERT" in broadcast_payload["message"]
        assert "tamper detected" in broadcast_payload["message"].lower()
        assert broadcast_payload["severity"] == "critical"
    
    @pytest.mark.asyncio
    async def test_emergency_lockdown_flow(self, integrated_system):
        """Test emergency lockdown functionality."""
        system = integrated_system
        
        reason = "Security breach detected in Building A"
        
        # Trigger emergency lockdown
        result = await system['device_service'].handle_emergency_lockdown(reason)
        
        assert result is True
        
        # Verify emergency command was published
        system['mqtt_adapter'].publish.assert_called()
        
        call_args = system['mqtt_adapter'].publish.call_args
        topic = call_args[0][0]
        payload_str = call_args[0][1]
        qos = call_args[1]['qos']
        
        assert topic == "access/commands/emergency/lockdown"
        assert qos == 2  # High priority
        
        payload = json.loads(payload_str)
        assert payload["command"] == "emergency_lock"
        assert payload["reason"] == reason
        assert "timestamp" in payload
        assert "message_id" in payload
    
    @pytest.mark.asyncio
    async def test_concurrent_device_requests(self, integrated_system, sample_entities):
        """Test handling concurrent device requests."""
        system = integrated_system
        entities = sample_entities
        
        # Setup repository mocks
        system['repositories']['card_repository'].get_by_card_id.return_value = entities['card']
        system['repositories']['door_repository'].get_by_id.return_value = entities['door']
        system['repositories']['user_repository'].get_by_id.return_value = entities['user']
        system['repositories']['permission_repository'].check_access.return_value = True
        system['repositories']['card_repository'].update.return_value = None
        system['repositories']['door_repository'].update.return_value = None
        
        # Create multiple concurrent requests
        requests = []
        for i in range(5):
            topic = f"access/requests/door_lock_00{i+1}"
            payload = json.dumps({
                "card_id": "ABC123",
                "door_id": self.TEST_DOOR_ID,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message_id": str(uuid4())
            })
            requests.append((topic, payload))
        
        # Process all requests concurrently
        tasks = [
            system['device_handler'].handle_message(topic, payload)
            for topic, payload in requests
        ]
        await asyncio.gather(*tasks)
        
        # Verify all requests were processed
        assert system['repositories']['card_repository'].get_by_card_id.call_count == 5
        assert system['repositories']['door_repository'].get_by_id.call_count == 5
        assert system['repositories']['user_repository'].get_by_id.call_count == 5
        
        # Verify responses were sent for all devices
        response_count = 0
        for call in system['mqtt_adapter'].publish.call_args_list:
            if "access/responses/" in call[0][0]:
                response_count += 1
        
        assert response_count == 5


class TestErrorHandlingIntegration:
    """Integration tests for error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_mqtt_publish_failure_handling(self, integrated_system, sample_entities):
        """Test handling of MQTT publish failures."""
        system = integrated_system
        entities = sample_entities
        
        # Make MQTT publish fail
        system['mqtt_adapter'].publish.side_effect = Exception("MQTT broker unavailable")
        
        # Setup successful validation
        system['repositories']['card_repository'].get_by_card_id.return_value = entities['card']
        system['repositories']['door_repository'].get_by_id.return_value = entities['door']
        system['repositories']['user_repository'].get_by_id.return_value = entities['user']
        system['repositories']['permission_repository'].check_access.return_value = True
        system['repositories']['card_repository'].update.return_value = None
        system['repositories']['door_repository'].update.return_value = None
        
        # Process request (should not crash despite MQTT failure)
        topic = "access/requests/door_lock_001"
        payload = json.dumps({
            "card_id": "ABC123",
            "door_id": self.TEST_DOOR_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_id": str(uuid4())
        })
        
        # Should not raise exception
        await system['device_handler'].handle_message(topic, payload)
        
        # Validation should still have occurred
        system['repositories']['card_repository'].get_by_card_id.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_database_failure_handling(self, integrated_system):
        """Test handling of database failures."""
        system = integrated_system
        
        # Make database calls fail
        system['repositories']['card_repository'].get_by_card_id.side_effect = Exception("Database connection lost")
        
        # Process request
        topic = "access/requests/door_lock_001"
        payload = json.dumps({
            "card_id": "ABC123",
            "door_id": self.TEST_DOOR_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_id": str(uuid4())
        })
        
        # Should not raise exception, should send denial response
        await system['device_handler'].handle_message(topic, payload)
        
        # Should attempt to send denial response
        denial_response_sent = False
        for call in system['mqtt_adapter'].publish.call_args_list:
            if "access/responses/" in call[0][0]:
                response_payload = json.loads(call[0][1])
                if not response_payload.get("access_granted", True):
                    denial_response_sent = True
                    break
        
        assert denial_response_sent, "Denial response should be sent on database failure"
    
    @pytest.mark.asyncio
    async def test_malformed_message_handling(self, integrated_system):
        """Test handling of malformed MQTT messages."""
        system = integrated_system
        
        malformed_payloads = [
            "not json",
            '{"incomplete": }',
            '{"card_id": "ABC123"}',  # Missing door_id
            json.dumps({"card_id": "", "door_id": "not_int"}),  # Invalid types
            ""  # Empty payload
        ]
        
        for payload in malformed_payloads:
            topic = "access/requests/door_lock_001"
            
            # Should not raise exception
            await system['device_handler'].handle_message(topic, payload)
        
        # No access validation should have been attempted
        system['repositories']['card_repository'].get_by_card_id.assert_not_called()


class TestPerformanceIntegration:
    """Integration tests for performance scenarios."""
    
    @pytest.mark.asyncio
    async def test_high_throughput_message_processing(self, integrated_system, sample_entities):
        """Test system performance under high message throughput."""
        system = integrated_system
        entities = sample_entities
        
        # Setup fast repository responses
        system['repositories']['card_repository'].get_by_card_id.return_value = entities['card']
        system['repositories']['door_repository'].get_by_id.return_value = entities['door']
        system['repositories']['user_repository'].get_by_id.return_value = entities['user']
        system['repositories']['permission_repository'].check_access.return_value = True
        system['repositories']['card_repository'].update.return_value = None
        system['repositories']['door_repository'].update.return_value = None
        
        # Generate many messages
        message_count = 100
        tasks = []
        
        for i in range(message_count):
            topic = f"access/requests/door_lock_{i % 10:03d}"
            payload = json.dumps({
                "card_id": f"CARD_{i:03d}",
                "door_id": (i % 5) + 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message_id": str(uuid4())
            })
            
            task = system['device_handler'].handle_message(topic, payload)
            tasks.append(task)
        
        # Process all messages concurrently
        start_time = datetime.now(timezone.utc)
        await asyncio.gather(*tasks)
        end_time = datetime.now(timezone.utc)
        
        processing_time = (end_time - start_time).total_seconds()
        
        # Verify reasonable performance (should process 100 messages in under 10 seconds)
        assert processing_time < 10, f"Processing took {processing_time} seconds, expected < 10"
        
        # Verify all messages were processed
        assert system['repositories']['card_repository'].get_by_card_id.call_count == message_count
        
        print(f"Processed {message_count} messages in {processing_time:.2f} seconds")
        print(f"Throughput: {message_count / processing_time:.2f} messages/second")