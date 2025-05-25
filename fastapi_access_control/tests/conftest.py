# app/tests/conftest.py
import pytest
import asyncio
from typing import List, Tuple, Any, Dict
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from datetime import datetime, UTC

from app.main import app
from app.adapters.persistence.models import Base
from app.infrastructure.persistence.adapters.sqlalchemy_mqtt_repository import SqlAlchemyMqttMessageRepository
from app.domain.entities.user import User, Role, UserStatus
from app.domain.services.auth_service import AuthService
from app.domain.value_objects.auth import UserClaims

# Test Database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(test_db):
    """Create database session for tests"""
    async_session = sessionmaker(
        test_db, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

@pytest.fixture
async def mqtt_repository(test_db):
    """Create MQTT repository for tests"""
    async_session = async_sessionmaker(
        test_db, class_=AsyncSession, expire_on_commit=False
    )
    repository = SqlAlchemyMqttMessageRepository(async_session)
    yield repository

class MockMQTTClient:
    """Mock MQTT Client for testing"""
    
    def __init__(self):
        self.published_messages: List[Tuple[str, str, int]] = []
        self.subscribed_topics: List[str] = []
        self.connected = False
        self.client = MagicMock()
    
    async def connect(self):
        """Mock connect"""
        self.connected = True
    
    async def disconnect(self):
        """Mock disconnect"""
        self.connected = False
        self.published_messages.clear()
        self.subscribed_topics.clear()
    
    async def publish(self, topic: str, payload: str, qos: int = 1, retain: bool = False):
        """Mock publish - stores message for verification"""
        self.published_messages.append((topic, payload, qos))
    
    async def subscribe(self, topic: str, qos: int = 1):
        """Mock subscribe"""
        self.subscribed_topics.append(topic)
    
    async def publish_door_event(self, door_id: str, event_data: Dict[str, Any]):
        """Mock publish door event"""
        import json
        topic = f"access/doors/{door_id}/events"
        payload = json.dumps(event_data)
        await self.publish(topic, payload, qos=1)
    
    async def publish_card_scan(self, card_id: str, scan_data: Dict[str, Any]):
        """Mock publish card scan"""
        import json
        topic = f"access/cards/{card_id}/scans"
        payload = json.dumps(scan_data)
        await self.publish(topic, payload, qos=1)
    
    async def send_device_command(self, device_id: str, command: Dict[str, Any]):
        """Mock send device command"""
        import json
        topic = f"access/commands/{device_id}"
        payload = json.dumps(command)
        await self.publish(topic, payload, qos=2)
    
    def get_last_published_message(self) -> Tuple[str, str, int]:
        """Get the last published message"""
        if not self.published_messages:
            raise AssertionError("No messages have been published")
        return self.published_messages[-1]
    
    def get_published_message(self, index: int = 0) -> Tuple[str, str, int]:
        """Get published message by index"""
        if index >= len(self.published_messages):
            raise AssertionError(f"Message index {index} out of range. Only {len(self.published_messages)} messages published.")
        return self.published_messages[index]
    
    def assert_message_published(self, topic: str, payload: str, qos: int = 1):
        """Assert that a specific message was published"""
        message_found = any(
            msg[0] == topic and msg[1] == payload and msg[2] == qos
            for msg in self.published_messages
        )
        if not message_found:
            raise AssertionError(
                f"Message not found: topic='{topic}', payload='{payload}', qos={qos}\n"
                f"Published messages: {self.published_messages}"
            )
    
    def assert_topic_published(self, topic: str):
        """Assert that a message was published to a specific topic"""
        topics_published = [msg[0] for msg in self.published_messages]
        if topic not in topics_published:
            raise AssertionError(
                f"No message published to topic '{topic}'\n"
                f"Topics published to: {topics_published}"
            )
    
    def clear_published_messages(self):
        """Clear all published messages"""
        self.published_messages.clear()

@pytest.fixture
def mock_mqtt_client():
    """Provide mock MQTT client for testing"""
    return MockMQTTClient()

@pytest.fixture
async def mqtt_client_connected(mock_mqtt_client):
    """Provide connected mock MQTT client"""
    await mock_mqtt_client.connect()
    yield mock_mqtt_client
    await mock_mqtt_client.disconnect()

@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)

# Utility functions for tests
@pytest.fixture
def sample_door_event():
    """Sample door event data"""
    return {
        "door_id": "main_entrance",
        "event_type": "card_scanned",
        "card_id": "emp_12345",
        "timestamp": "2024-01-01T10:00:00Z",
        "status": "access_granted",
        "user_id": "user_123"
    }

@pytest.fixture
def sample_card_scan():
    """Sample card scan data"""
    return {
        "card_id": "emp_12345",
        "door_id": "main_entrance",
        "timestamp": "2024-01-01T10:00:00Z",
        "signal_strength": -45,
        "reader_id": "reader_001"
    }

@pytest.fixture
def sample_device_command():
    """Sample device command"""
    return {
        "action": "unlock_door",
        "duration": 5,
        "timestamp": "2024-01-01T10:00:00Z",
        "request_id": "cmd_123"
    }

@pytest.fixture
def sample_user():
    """Sample user for testing"""
    return User(
        id=1,
        email="test@example.com",
        hashed_password="$2b$12$test.hash.here",
        full_name="Test User",
        roles=[Role.USER],
        status=UserStatus.ACTIVE,
        created_at=datetime.now(UTC)
    )

@pytest.fixture
def sample_admin_user():
    """Sample admin user for testing"""
    return User(
        id=2,
        email="admin@example.com",
        hashed_password="$2b$12$admin.hash.here",
        full_name="Admin User",
        roles=[Role.ADMIN, Role.OPERATOR],
        status=UserStatus.ACTIVE,
        created_at=datetime.now(UTC)
    )

@pytest.fixture
def auth_service():
    """AuthService instance for testing"""
    return AuthService()

@pytest.fixture
def mock_user_repository():
    """Mock user repository for testing"""
    return AsyncMock()

@pytest.fixture
def valid_jwt_token(auth_service, sample_user):
    """Valid JWT token for testing"""
    return auth_service.generate_access_token(sample_user)

@pytest.fixture
def valid_user_claims():
    """Valid user claims for testing"""
    return UserClaims(
        user_id=1,
        email="test@example.com",
        full_name="Test User",
        roles=["user"]
    )

@pytest.fixture
def admin_user_claims():
    """Admin user claims for testing"""
    return UserClaims(
        user_id=2,
        email="admin@example.com",
        full_name="Admin User",
        roles=["admin", "operator"]
    )