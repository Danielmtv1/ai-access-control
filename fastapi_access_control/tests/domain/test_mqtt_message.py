import pytest
from datetime import datetime
from app.domain.entities.mqtt_message import MqttMessage

def test_mqtt_message_creation():
    """Test that domain entity is pure"""
    message = MqttMessage.create("test/topic", "test message")
    
    assert message.topic == "test/topic"
    assert message.message == "test message"
    assert message.id is None
    assert isinstance(message.timestamp, datetime)

def test_mqtt_message_validation():
    """Test business rule validations"""
    # Test empty topic
    with pytest.raises(ValueError, match="Topic cannot be empty"):
        MqttMessage.create("", "message")
    
    # Test empty message
    with pytest.raises(ValueError, match="Message cannot be empty"):
        MqttMessage.create("topic", "")
    
    # Test wildcard characters in topic
    with pytest.raises(ValueError, match="Topic cannot contain wildcard characters"):
        MqttMessage.create("test/#", "message")
    
    with pytest.raises(ValueError, match="Topic cannot contain wildcard characters"):
        MqttMessage.create("test/+/message", "message")

def test_mqtt_message_immutability():
    """Test that MqttMessage is immutable"""
    message = MqttMessage.create("test/topic", "test message")
    
    with pytest.raises(dataclasses.FrozenInstanceError):
        message.topic = "new/topic"
    
    with pytest.raises(dataclasses.FrozenInstanceError):
        message.message = "new message" 