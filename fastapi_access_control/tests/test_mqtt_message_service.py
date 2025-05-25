import pytest
from app.domain.entities.mqtt_message import MqttMessage
from app.domain.services import MqttMessageService
from app.infrastructure.persistence.adapters.sqlalchemy_mqtt_repository import SqlAlchemyMqttMessageRepository

@pytest.mark.asyncio
async def test_save_mqtt_message(async_session):
    """Test that the MqttMessageService can save a message to the database."""
    # Arrange
    repository = SqlAlchemyMqttMessageRepository(session_factory=lambda: async_session)
    service = MqttMessageService(repository=repository)
    message = MqttMessage(topic="test_topic", message="test_message")

    # Act
    saved_message = await service.process_mqtt_message(message.topic, message.message)

    # Assert
    assert saved_message is not None
    assert saved_message.topic == message.topic
    assert saved_message.message == message.message
    assert saved_message.id is not None

@pytest.mark.asyncio
async def test_get_all_mqtt_messages(async_session):
    """Test that the MqttMessageService can retrieve all messages from the database."""
    # Arrange
    repository = SqlAlchemyMqttMessageRepository(session_factory=lambda: async_session)
    service = MqttMessageService(repository=repository)
    message1 = MqttMessage(topic="test_topic_1", message="test_message_1")
    message2 = MqttMessage(topic="test_topic_2", message="test_message_2")
    await service.process_mqtt_message(message1.topic, message1.message)
    await service.process_mqtt_message(message2.topic, message2.message)

    # Act
    messages = await service.get_all_messages()

    # Assert
    assert len(messages) == 2
    assert messages[0].topic == message1.topic
    assert messages[0].message == message1.message
    assert messages[1].topic == message2.topic
    assert messages[1].message == message2.message 