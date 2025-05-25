import pytest
from datetime import datetime
from app.domain.entities.mqtt_message import MqttMessage
from app.infrastructure.database.models.mqtt_message import MqttMessageModel
from app.infrastructure.persistence.mappers.mqtt_message_mapper import MqttMessageMapper

def test_mapper_to_domain():
    """Test conversion from infrastructure model to domain entity"""
    # Create test model
    model = MqttMessageModel(
        id=1,
        topic="test/topic",
        message="test message",
        timestamp=datetime.utcnow()
    )
    
    # Convert to domain entity
    domain_entity = MqttMessageMapper.to_domain(model)
    
    # Verify conversion
    assert isinstance(domain_entity, MqttMessage)
    assert domain_entity.id == model.id
    assert domain_entity.topic == model.topic
    assert domain_entity.message == model.message
    assert domain_entity.timestamp == model.timestamp

def test_mapper_to_model():
    """Test conversion from domain entity to infrastructure model"""
    # Create test domain entity
    domain_entity = MqttMessage.create(
        topic="test/topic",
        message="test message"
    )
    
    # Convert to model
    model = MqttMessageMapper.to_model(domain_entity)
    
    # Verify conversion
    assert isinstance(model, MqttMessageModel)
    assert model.topic == domain_entity.topic
    assert model.message == domain_entity.message
    assert model.timestamp == domain_entity.timestamp
    assert model.id is None  # New entity should not have ID 