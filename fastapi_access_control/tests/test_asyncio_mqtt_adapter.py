# app/tests/adapters/test_mqtt_client.py
import pytest
import json
from app.adapters.messaging.topics_manager import MQTTTopicsManager

class TestMQTTClient:
    """Tests para MQTT Client"""
    
    @pytest.mark.asyncio
    async def test_publish_door_event(self, mock_mqtt_client, sample_door_event):
        """Test publishing door event"""
        door_id = "main_entrance"
        
        # Act
        await mock_mqtt_client.publish_door_event(door_id, sample_door_event)
        
        # Assert - Forma correcta de acceder al mensaje
        assert len(mock_mqtt_client.published_messages) == 1
        
        topic, payload, qos = mock_mqtt_client.get_published_message(0)
        expected_topic = f"access/doors/{door_id}/events"
        expected_payload = json.dumps(sample_door_event)
        
        assert topic == expected_topic
        assert payload == expected_payload
        assert qos == 1
    
    @pytest.mark.asyncio
    async def test_publish_card_scan(self, mock_mqtt_client, sample_card_scan):
        """Test publishing card scan"""
        card_id = "emp_12345"
        
        # Act
        await mock_mqtt_client.publish_card_scan(card_id, sample_card_scan)
        
        # Assert - Usando método helper
        expected_topic = f"access/cards/{card_id}/scans"
        expected_payload = json.dumps(sample_card_scan)
        
        mock_mqtt_client.assert_message_published(expected_topic, expected_payload, qos=1)
    
    @pytest.mark.asyncio
    async def test_send_device_command(self, mock_mqtt_client, sample_device_command):
        """Test sending device command"""
        device_id = "lock_001"
        
        # Act
        await mock_mqtt_client.send_device_command(device_id, sample_device_command)
        
        # Assert - Verificar topic específico
        expected_topic = f"access/commands/{device_id}"
        mock_mqtt_client.assert_topic_published(expected_topic)
        
        # Verificar mensaje completo
        topic, payload, qos = mock_mqtt_client.get_last_published_message()
        assert topic == expected_topic
        assert json.loads(payload) == sample_device_command
        assert qos == 2  # QoS 2 para comandos críticos
    
    @pytest.mark.asyncio
    async def test_multiple_messages(self, mock_mqtt_client, sample_door_event, sample_card_scan):
        """Test publishing multiple messages"""
        # Act
        await mock_mqtt_client.publish_door_event("door_1", sample_door_event)
        await mock_mqtt_client.publish_card_scan("card_1", sample_card_scan)
        
        # Assert
        assert len(mock_mqtt_client.published_messages) == 2
        
        # Verificar primer mensaje
        topic1, payload1, qos1 = mock_mqtt_client.get_published_message(0)
        assert topic1 == "access/doors/door_1/events"
        assert json.loads(payload1) == sample_door_event
        
        # Verificar segundo mensaje
        topic2, payload2, qos2 = mock_mqtt_client.get_published_message(1)
        assert topic2 == "access/cards/card_1/scans"
        assert json.loads(payload2) == sample_card_scan
    
    @pytest.mark.asyncio
    async def test_connection_lifecycle(self, mock_mqtt_client):
        """Test connection lifecycle"""
        # Initial state
        assert not mock_mqtt_client.connected
        
        # Connect
        await mock_mqtt_client.connect()
        assert mock_mqtt_client.connected
        
        # Disconnect
        await mock_mqtt_client.disconnect()
        assert not mock_mqtt_client.connected
        assert len(mock_mqtt_client.published_messages) == 0
    
    @pytest.mark.asyncio
    async def test_subscription(self, mock_mqtt_client):
        """Test topic subscription"""
        topics = [
            "access/doors/+/events",
            "access/cards/+/scans",
            "access/status/+"
        ]
        
        # Act
        for topic in topics:
            await mock_mqtt_client.subscribe(topic)
        
        # Assert
        assert mock_mqtt_client.subscribed_topics == topics
    
    def test_assert_helpers(self, mock_mqtt_client):
        """Test assertion helper methods"""
        # Preparar datos
        topic = "test/topic"
        payload = json.dumps({"test": "data"})
        qos = 1
        
        # Simular publicación manual
        mock_mqtt_client.published_messages.append((topic, payload, qos))
        
        # Test assertion helpers
        mock_mqtt_client.assert_topic_published(topic)
        mock_mqtt_client.assert_message_published(topic, payload, qos)
        
        # Test error cases
        with pytest.raises(AssertionError):
            mock_mqtt_client.assert_topic_published("nonexistent/topic")
        
        with pytest.raises(AssertionError):
            mock_mqtt_client.assert_message_published(topic, "wrong_payload", qos)

class TestMQTTTopicsManager:
    """Tests para Topics Manager"""
    
    def test_get_door_events_topic(self):
        """Test door events topic generation"""
        door_id = "main_entrance"
        expected = "access/doors/main_entrance/events"
        
        result = MQTTTopicsManager.get_door_events_topic(door_id)
        assert result == expected
    
    def test_get_card_scans_topic(self):
        """Test card scans topic generation"""
        card_id = "emp_12345"
        expected = "access/cards/emp_12345/scans"
        
        result = MQTTTopicsManager.get_card_scans_topic(card_id)
        assert result == expected
    
    def test_parse_topic(self):
        """Test topic parsing"""
        topic = "access/doors/main_entrance/events"
        
        result = MQTTTopicsManager.parse_topic(topic)
        assert result == {
            "type": "doors",
            "id": "main_entrance",
            "action": "events"
        }
    
    def test_validate_topic(self):
        """Test topic validation"""
        valid_topics = [
            "access/doors/main/events",
            "access/cards/123/scans",
            "access/commands/device1",
            "access/status/device1"
        ]
        
        invalid_topics = [
            "invalid/doors/main/events",
            "access",
            "doors/main/events",
            ""
        ]
        
        for topic in valid_topics:
            assert MQTTTopicsManager.validate_topic(topic), f"Topic should be valid: {topic}"
        
        for topic in invalid_topics:
            assert not MQTTTopicsManager.validate_topic(topic), f"Topic should be invalid: {topic}"