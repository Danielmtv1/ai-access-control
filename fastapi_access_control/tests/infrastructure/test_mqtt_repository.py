import pytest
from datetime import datetime, timezone, UTC
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domain.entities.mqtt_message import MqttMessage
from app.infrastructure.persistence.adapters.sqlalchemy_mqtt_repository import SqlAlchemyMqttMessageRepository
from app.infrastructure.database.models.mqtt_message import MqttMessageModel
from app.domain.exceptions import RepositoryError

@pytest.fixture
def mock_session():
    """Create a mock session"""
    session = AsyncMock(spec=AsyncSession)
    return session

@pytest.fixture
def mock_session_factory(mock_session):
    """Create a mock session factory"""
    factory = MagicMock()
    factory.return_value.__aenter__.return_value = mock_session
    return factory

@pytest.fixture
def repository(mock_session_factory):
    """Create repository instance with mock session factory"""
    return SqlAlchemyMqttMessageRepository(mock_session_factory)

@pytest.mark.asyncio
async def test_save_message(repository, mock_session):
    """Test saving a message"""
    # Create test message
    message = MqttMessage.create("test/topic", "test message")
    
    # Mock session behavior
    mock_session.add = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    
    # Mock the model after refresh
    mock_model = MqttMessageModel(
        id=SAMPLE_CARD_UUID,
        topic=message.topic,
        message=message.message,
        timestamp=message.timestamp
    )
    mock_session.refresh.return_value = mock_model
    
    # Save message
    saved_message = await repository.save(message)
    
    # Verify behavior
    assert isinstance(saved_message, MqttMessage)
    assert saved_message.id == 1
    assert saved_message.topic == message.topic
    assert saved_message.message == message.message
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_get_all_messages(repository, mock_session):
    """Test getting all messages"""
    # Create test models
    models = [
        MqttMessageModel(
            id=SAMPLE_CARD_UUID,
            topic="test/topic1",
            message="message1",
            timestamp=datetime.now(UTC)
        ),
        MqttMessageModel(
            id=SAMPLE_CARD_UUID_2,
            topic="test/topic2",
            message="message2",
            timestamp=datetime.now(UTC)
        )
    ]
    
    # Mock session behavior
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = models
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    # Get messages
    messages = await repository.get_all()
    
    # Verify behavior
    assert len(messages) == 2
    assert all(isinstance(msg, MqttMessage) for msg in messages)
    assert messages[0].id == 1
    assert messages[1].id == 2
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_message_by_id(repository, mock_session):
    """Test getting message by ID"""
    # Create test model
    model = MqttMessageModel(
        id=SAMPLE_CARD_UUID,
        topic="test/topic",
        message="test message",
        timestamp=datetime.now(UTC)
    )
    
    # Mock session behavior
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = model
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    # Get message
    message = await repository.get_by_id(1)
    
    # Verify behavior
    assert isinstance(message, MqttMessage)
    assert message.id == 1
    assert message.topic == model.topic
    assert message.message == model.message
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_messages_by_topic(repository, mock_session):
    """Test getting messages by topic"""
    # Create test models
    models = [
        MqttMessageModel(
            id=SAMPLE_CARD_UUID,
            topic="test/topic",
            message="message1",
            timestamp=datetime.now(UTC)
        ),
        MqttMessageModel(
            id=SAMPLE_CARD_UUID_2,
            topic="test/topic",
            message="message2",
            timestamp=datetime.now(UTC)
        )
    ]
    
    # Mock session behavior
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = models
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    # Get messages
    messages = await repository.get_by_topic("test/topic")
    
    # Verify behavior
    assert len(messages) == 2
    assert all(isinstance(msg, MqttMessage) for msg in messages)
    assert all(msg.topic == "test/topic" for msg in messages)
    mock_session.execute.assert_called_once() 