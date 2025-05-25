import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from app.domain.mqtt_message import MqttMessage
from app.infrastructure.persistence.adapters.sqlalchemy_mqtt_repository import SqlAlchemyMqttMessageRepository
from app.domain.exceptions import RepositoryError

# Fixture for AsyncSession mock
@pytest.fixture
def mock_async_session():
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session

# Fixture for session factory mock
@pytest.fixture
def mock_session_factory(mock_async_session):
    factory = AsyncMock()
    factory.return_value.__aenter__.return_value = mock_async_session
    return factory

# Fixture for repository
@pytest.fixture
def repository(mock_session_factory):
    return SqlAlchemyMqttMessageRepository(mock_session_factory)

# Unit tests
@pytest.mark.asyncio
async def test_save_message_success(repository, mock_async_session):
    # Arrange
    message = MqttMessage(
        topic="test/topic",
        message="test message",
        timestamp=datetime.now()
    )
    
    # Act
    result = await repository.save(message)
    
    # Assert
    assert result == message
    mock_async_session.add.assert_called_once_with(message)
    mock_async_session.commit.assert_called_once()
    mock_async_session.refresh.assert_called_once_with(message)

@pytest.mark.asyncio
async def test_save_message_database_error(repository, mock_async_session):
    # Arrange
    message = MqttMessage(
        topic="test/topic",
        message="test message",
        timestamp=datetime.now()
    )
    mock_async_session.commit.side_effect = Exception("Database error")
    
    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.save(message)
    assert "Error saving MQTT message" in str(exc_info.value)
    mock_async_session.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_get_all_messages_success(repository, mock_async_session):
    # Arrange
    messages = [
        MqttMessage(topic="test/topic1", message="message1", timestamp=datetime.now()),
        MqttMessage(topic="test/topic2", message="message2", timestamp=datetime.now())
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = messages
    mock_async_session.execute.return_value = mock_result
    
    # Act
    result = await repository.get_all()
    
    # Assert
    assert result == messages
    mock_async_session.execute.assert_called_once()
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_get_all_messages_database_error(repository, mock_async_session):
    # Arrange
    mock_async_session.execute.side_effect = Exception("Database error")
    
    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.get_all()
    assert "Error retrieving MQTT messages" in str(exc_info.value)

# Integration tests
@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_save_and_get_message():
    # This test requires a real database
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.config import get_settings
    
    # Configure test database
    settings = get_settings()
    test_db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(test_db_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    # Create repository
    repository = SqlAlchemyMqttMessageRepository(async_session)
    
    # Create and save a message
    message = MqttMessage(
        topic="integration/test",
        message="integration test message",
        timestamp=datetime.now()
    )
    
    try:
        # Act
        saved_message = await repository.save(message)
        retrieved_messages = await repository.get_all()
        
        # Assert
        assert saved_message.id is not None
        assert len(retrieved_messages) > 0
        assert any(m.id == saved_message.id for m in retrieved_messages)
        
    finally:
        # Cleanup
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: sync_conn.execute("DELETE FROM mqtt_messages")) 