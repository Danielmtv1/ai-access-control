# app/tests/conftest.py
import pytest
import asyncio
import os
from typing import List, Tuple, Any, Dict
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient
from datetime import datetime, timezone, UTC, timedelta, time
from uuid import UUID, uuid4

from app.shared.database.base import Base
from app.infrastructure.persistence.adapters.sqlalchemy_mqtt_repository import SqlAlchemyMqttMessageRepository
from app.domain.entities.user import User, Role, UserStatus
from app.domain.services.auth_service import AuthService
from app.domain.value_objects.auth import UserClaims
from app.domain.entities.mqtt_message import MqttMessage
from app.domain.entities.card import Card, CardType, CardStatus
from app.domain.entities.door import Door, DoorType, SecurityLevel, DoorStatus, AccessSchedule
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.models.card import CardModel
from app.infrastructure.database.models.door import DoorModel

# Test UUIDs for consistent testing
SAMPLE_USER_UUID = UUID("12345678-1234-5678-9012-123456789012")
SAMPLE_ADMIN_UUID = UUID("87654321-4321-8765-2109-876543210987")  
SAMPLE_CARD_UUID = UUID("11111111-2222-3333-4444-555555555555")
SAMPLE_CARD_UUID_2 = UUID("22222222-3333-4444-5555-666666666666")
SAMPLE_DOOR_UUID = UUID("66666666-7777-8888-9999-000000000000")
SAMPLE_DOOR_UUID_2 = UUID("77777777-8888-9999-0000-111111111111")

# Test Database
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@db:5432/postgres_test"
)

@pytest.fixture(scope="session")
def event_loop():
    """
    Creates and yields a new asyncio event loop for the duration of the test session.
    
    Yields:
        The newly created asyncio event loop, which is closed after the session ends.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    """
    Creates a fresh asynchronous SQLAlchemy engine for the test database.
    
    Drops all tables before and after the test session to ensure a clean database state. Yields the engine for use in tests and disposes of it after completion.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(test_db):
    """
    Provides an asynchronous SQLAlchemy session for database operations during tests.
    
    Yields:
        An AsyncSession instance scoped to the test, which is closed after use.
    """
    async_session = async_sessionmaker(
        test_db, class_=AsyncSession, expire_on_commit=False
    )
    session = async_session()
    try:
        yield session
    finally:
        await session.close()

@pytest.fixture
async def mqtt_repository(db_session):
    """
    Creates a SQLAlchemy-based MQTT message repository for testing.
    
    Args:
        db_session: The SQLAlchemy async session used for database operations.
    
    Returns:
        An instance of SqlAlchemyMqttMessageRepository configured with the provided session.
    """
    repository = SqlAlchemyMqttMessageRepository(db_session)
    return repository

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
    """
    Provides a connected instance of the mock MQTT client for testing.
    
    The client is connected before being returned, allowing tests to interact with a simulated MQTT broker.
    """
    await mock_mqtt_client.connect()
    return mock_mqtt_client

@pytest.fixture
async def client(db_session):
    """
    Provides an asynchronous FastAPI test client with the database dependency overridden to use the test session.
    
    Yields:
        An `httpx.AsyncClient` instance configured for testing FastAPI endpoints with the test database session.
    """
    from app.main import app
    from app.shared.database.session import get_db
    
    # Override the database dependency to use test session
    async def override_get_db():
        Yields the test database session for dependency injection during tests.
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # Clean up the override after the test
    del app.dependency_overrides[get_db]

@pytest.fixture
async def auth_service():
    """
    Provides an AuthService instance for use in authentication-related tests.
    """
    return AuthService()

@pytest.fixture
async def admin_user(db_session: AsyncSession, auth_service: AuthService):
    """
    Creates and persists an active admin user in the test database.
    
    The user is initialized with a hashed password, admin role, and current timestamps, and is committed to the provided async database session.
    
    Returns:
        The created UserModel instance representing the admin user.
    """
    hashed_password = auth_service.hash_password("AdminPassword123!")
    user_model = UserModel(
        email="admin@test.com",
        hashed_password=hashed_password,
        full_name="Admin User",
        roles=["admin"],
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(user_model)
    await db_session.commit()
    await db_session.refresh(user_model)
    return user_model

@pytest.fixture
async def auth_headers(admin_user: UserModel, auth_service: AuthService):
    """
    Generates authentication headers with a bearer token for the given admin user.
    
    Args:
        admin_user: The admin user model for whom the token is generated.
        auth_service: The authentication service used to generate the token.
    
    Returns:
        A dictionary containing the Authorization header with a bearer token.
    """
    token_pair = auth_service.generate_token_pair(
        user_id=str(admin_user.id),
        email=admin_user.email,
        roles=admin_user.roles
    )
    return {"Authorization": f"Bearer {token_pair.access_token}"}

@pytest.fixture
async def test_employee_user(db_session: AsyncSession):
    """
    Creates and persists an active employee user in the test database for access control tests.
    
    Returns:
        The created UserModel instance representing the employee user.
    """
    user_model = UserModel(
        email="employee@test.com",
        hashed_password="hashed_password",
        full_name="Employee User",
        roles=["user"],
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(user_model)
    await db_session.commit()
    await db_session.refresh(user_model)
    return user_model

@pytest.fixture
async def test_doors(db_session: AsyncSession):
    """
    Creates and persists multiple test door records with varying security levels and statuses.
    
    Returns:
        A list of DoorModel instances representing the created doors.
    """
    doors = []
    
    # Regular office door
    office_door = DoorModel(
        name="Office Door",
        location="Building A - Floor 1",
        security_level="low",
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Server room with high security
    server_door = DoorModel(
        name="Server Room",
        location="Building A - Basement",
        security_level="high",
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Maintenance door
    maintenance_door = DoorModel(
        name="Maintenance Room",
        location="Building A - Basement",
        security_level="medium",
        status="maintenance",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    doors.extend([office_door, server_door, maintenance_door])
    
    for door in doors:
        db_session.add(door)
    
    await db_session.commit()
    
    for door in doors:
        await db_session.refresh(door)
    
    return doors

@pytest.fixture
async def test_cards(db_session: AsyncSession, test_employee_user: UserModel):
    """
    Creates and persists multiple test card records for an employee user.
    
    This fixture adds an active employee card, a suspended employee card, and an active master card to the database for use in test scenarios.
    
    Returns:
        A list of CardModel instances representing the created cards.
    """
    cards = []
    
    # Active employee card
    active_card = CardModel(
        user_id=test_employee_user.id,
        card_id="EMP001",
        card_type="employee",
        status="active",
        valid_from=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Suspended card
    suspended_card = CardModel(
        user_id=test_employee_user.id,
        card_id="EMP002",
        card_type="employee",
        status="suspended",
        valid_from=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Master card
    master_card = CardModel(
        user_id=test_employee_user.id,
        card_id="MASTER001",
        card_type="master",
        status="active",
        valid_from=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    cards.extend([active_card, suspended_card, master_card])
    
    for card in cards:
        db_session.add(card)
    
    await db_session.commit()
    
    for card in cards:
        await db_session.refresh(card)
    
    return cards

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
        id=SAMPLE_USER_UUID,
        email="test@example.com",
        hashed_password="$2b$12$test.hash.here",
        full_name="Test User",
        roles=[Role.USER],
        status=UserStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )

@pytest.fixture
def sample_admin_user():
    """
    Creates and returns a sample admin user domain entity for testing purposes.
    
    The returned user has admin and operator roles, active status, and preset metadata.
    """
    return User(
        id=SAMPLE_ADMIN_UUID,
        email="admin@example.com",
        hashed_password="$2b$12$admin.hash.here",
        full_name="Admin User",
        roles=[Role.ADMIN, Role.OPERATOR],
        status=UserStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )

@pytest.fixture
def valid_jwt_token(auth_service, sample_user):
    """
    Generates a valid JWT access token for the provided sample user.
    
    Args:
        sample_user: The user entity for whom the token is generated.
    
    Returns:
        A JWT access token string for authentication in tests.
    """
    return auth_service.generate_access_token(sample_user)

@pytest.fixture
def valid_user_claims():
    """Valid user claims for testing"""
    return UserClaims(
        user_id=SAMPLE_USER_UUID,
        email="test@example.com",
        full_name="Test User",
        roles=["user"]
    )

@pytest.fixture
def admin_user_claims():
    """Admin user claims for testing"""
    return UserClaims(
        user_id=SAMPLE_ADMIN_UUID,
        email="admin@example.com",
        full_name="Admin User",
        roles=["admin", "operator"]
    )

@pytest.fixture
def sample_card():
    """Sample card for testing"""
    now = datetime.now(UTC)
    return Card(
        id=SAMPLE_CARD_UUID,
        card_id="CARD001",
        user_id=SAMPLE_USER_UUID,
        card_type=CardType.EMPLOYEE,
        status=CardStatus.ACTIVE,
        valid_from=now,
        valid_until=now + timedelta(days=365),
        created_at=now,
        updated_at=now,
        use_count=0
    )

@pytest.fixture
def sample_door():
    """Sample door for testing"""
    now = datetime.now(UTC)
    schedule = AccessSchedule(
        days_of_week=[0, 1, 2, 3, 4],
        start_time=time(9, 0),
        end_time=time(18, 0)
    )
    return Door(
        id=SAMPLE_DOOR_UUID,
        name="Main Entrance",
        location="Building A",
        door_type=DoorType.ENTRANCE,
        security_level=SecurityLevel.MEDIUM,
        status=DoorStatus.ACTIVE,
        created_at=now,
        updated_at=now,
        description="Main building entrance",
        default_schedule=schedule,
        requires_pin=False,
        max_attempts=3,
        lockout_duration=300,
        failed_attempts=0
    )