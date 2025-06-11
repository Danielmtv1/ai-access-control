"""
Tests for MQTT message service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, UTC

from app.domain.entities.mqtt_message import MqttMessage
from app.domain.services.mqtt_message_service import MqttMessageService
from app.domain.exceptions import RepositoryError


class TestMqttMessageService:
    """Tests for MqttMessageService"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock MQTT message repository"""
        return AsyncMock()
    
    @pytest.fixture
    def mqtt_service(self, mock_repository):
        """MQTT message service with mocked dependencies"""
        return MqttMessageService(mock_repository)
    
    @pytest.mark.asyncio
    async def test_save_message(self, mqtt_service, mock_repository):
        """Test saving MQTT message"""
        # Create test message
        message = MqttMessage(
            topic="test/topic",
            message="test payload",
            timestamp=datetime.now(UTC),
            id=123
        )
        
        # Configure mock
        mock_repository.save.return_value = message
        
        # Execute
        result = await mqtt_service.save_message(message)
        
        # Verify
        assert result == message
        mock_repository.save.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_save_message_repository_error(self, mqtt_service, mock_repository):
        """Test saving MQTT message with repository error"""
        message = MqttMessage(
            topic="test/topic",
            message="test payload",
            timestamp=datetime.now(UTC),
            id=123
        )
        
        # Configure mock to raise exception
        mock_repository.save.side_effect = Exception("Database error")
        
        # Execute and verify exception
        with pytest.raises(RepositoryError) as exc_info:
            await mqtt_service.save_message(message)
        
        assert "Error saving MQTT message" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_all_messages(self, mqtt_service, mock_repository):
        """Test getting all messages"""
        messages = [
            MqttMessage(
                topic="topic1",
                message="payload1",
                timestamp=datetime.now(UTC),
                id=1
            ),
            MqttMessage(
                topic="topic2",
                message="payload2",
                timestamp=datetime.now(UTC),
                id=2
            )
        ]
        
        # Configure mock
        mock_repository.get_all.return_value = messages
        
        # Execute
        result = await mqtt_service.get_all_messages()
        
        # Verify
        assert result == messages
        mock_repository.get_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_all_messages_repository_error(self, mqtt_service, mock_repository):
        """Test getting all messages with repository error"""
        # Configure mock to raise exception
        mock_repository.get_all.side_effect = Exception("Database error")
        
        # Execute and verify exception
        with pytest.raises(RepositoryError) as exc_info:
            await mqtt_service.get_all_messages()
        
        assert "Error retrieving MQTT messages" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_message_by_id(self, mqtt_service, mock_repository):
        """Test getting message by ID"""
        message_id = 123
        message = MqttMessage(
            topic="test/topic",
            message="test payload",
            timestamp=datetime.now(UTC),
            id=123
        )
        
        # Configure mock
        mock_repository.get_by_id.return_value = message
        
        # Execute
        result = await mqtt_service.get_message_by_id(message_id)
        
        # Verify
        assert result == message
        mock_repository.get_by_id.assert_called_once_with(message_id)
    
    @pytest.mark.asyncio
    async def test_get_message_by_id_not_found(self, mqtt_service, mock_repository):
        """Test getting message by ID when not found"""
        message_id = 999
        
        # Configure mock
        mock_repository.get_by_id.return_value = None
        
        # Execute
        result = await mqtt_service.get_message_by_id(message_id)
        
        # Verify
        assert result is None
        mock_repository.get_by_id.assert_called_once_with(message_id)
    
    @pytest.mark.asyncio
    async def test_get_message_by_id_repository_error(self, mqtt_service, mock_repository):
        """Test getting message by ID with repository error"""
        message_id = 123
        
        # Configure mock to raise exception
        mock_repository.get_by_id.side_effect = Exception("Database error")
        
        # Execute and verify exception
        with pytest.raises(RepositoryError) as exc_info:
            await mqtt_service.get_message_by_id(message_id)
        
        assert "Error retrieving MQTT message" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_messages_by_topic(self, mqtt_service, mock_repository):
        """Test getting messages by topic"""
        topic = "test/topic"
        messages = [
            MqttMessage(
                topic=topic,
                message="payload 1",
                timestamp=datetime.now(UTC),
                id=1
            ),
            MqttMessage(
                topic=topic,
                message="payload 2",
                timestamp=datetime.now(UTC),
                id=2
            )
        ]
        
        # Configure mock
        mock_repository.get_by_topic.return_value = messages
        
        # Execute
        result = await mqtt_service.get_messages_by_topic(topic)
        
        # Verify
        assert result == messages
        mock_repository.get_by_topic.assert_called_once_with(topic)
    
    @pytest.mark.asyncio
    async def test_get_messages_by_topic_repository_error(self, mqtt_service, mock_repository):
        """Test getting messages by topic with repository error"""
        topic = "test/topic"
        
        # Configure mock to raise exception
        mock_repository.get_by_topic.side_effect = Exception("Database error")
        
        # Execute and verify exception
        with pytest.raises(RepositoryError) as exc_info:
            await mqtt_service.get_messages_by_topic(topic)
        
        assert f"Error retrieving MQTT messages for topic {topic}" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('app.domain.entities.mqtt_message.MqttMessage.create')
    async def test_process_mqtt_message(self, mock_create, mqtt_service, mock_repository):
        """Test processing MQTT message"""
        topic = "test/topic"
        message_content = "test message"
        
        # Create mock message
        mock_message = MqttMessage(
            topic=topic,
            message=message_content,
            timestamp=datetime.now(UTC),
            id=123
        )
        
        # Configure mocks
        mock_create.return_value = mock_message
        mock_repository.save.return_value = mock_message
        
        # Execute
        await mqtt_service.process_mqtt_message(topic, message_content)
        
        # Verify
        mock_create.assert_called_once_with(topic=topic, message=message_content)
        mock_repository.save.assert_called_once_with(mock_message)
    
    @pytest.mark.asyncio
    @patch('app.domain.entities.mqtt_message.MqttMessage.create')
    async def test_process_mqtt_message_create_error(self, mock_create, mqtt_service, mock_repository):
        """Test processing MQTT message with creation error"""
        topic = "test/topic"
        message_content = "test message"
        
        # Configure mock to raise exception
        mock_create.side_effect = Exception("Creation error")
        
        # Execute and verify exception
        with pytest.raises(RepositoryError) as exc_info:
            await mqtt_service.process_mqtt_message(topic, message_content)
        
        assert "Error processing MQTT message" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('app.domain.entities.mqtt_message.MqttMessage.create')
    async def test_process_mqtt_message_save_error(self, mock_create, mqtt_service, mock_repository):
        """Test processing MQTT message with save error"""
        topic = "test/topic"
        message_content = "test message"
        
        # Create mock message
        mock_message = MqttMessage(
            topic=topic,
            message=message_content,
            timestamp=datetime.now(UTC),
            id=123
        )
        
        # Configure mocks
        mock_create.return_value = mock_message
        mock_repository.save.side_effect = Exception("Save error")
        
        # Execute and verify exception
        with pytest.raises(RepositoryError) as exc_info:
            await mqtt_service.process_mqtt_message(topic, message_content)
        
        assert "Error processing MQTT message" in str(exc_info.value)