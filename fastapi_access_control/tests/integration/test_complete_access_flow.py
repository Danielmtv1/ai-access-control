"""
Complete integration tests for access control flow.
Tests the entire system from API to database with real data.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, time
import json
from uuid import UUID

from app.main import app
from tests.conftest import (
    SAMPLE_USER_UUID, SAMPLE_CARD_UUID, SAMPLE_DOOR_UUID
)
from tests.seeders.integration_seeder import IntegrationSeeder
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.models.card import CardModel
from app.infrastructure.database.models.door import DoorModel
from app.infrastructure.database.models.permission import PermissionModel
from app.domain.services.auth_service import AuthService
from tests.conftest import MockMQTTClient

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def client(db_session):
    """
    Provides an HTTP async client for testing with the database dependency overridden to use the test session.
    
    Yields:
        An AsyncClient instance configured for the test application with the test database session.
    """
    from app.shared.database.session import get_db
    
    # Override the database dependency to use test session
    async def override_get_db():
        Yields the test database session for dependency injection in asynchronous test clients.
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # Clean up the override after the test
    del app.dependency_overrides[get_db]

@pytest.fixture
async def auth_service():
    """
    Provides an authentication service instance for use in tests.
    
    Returns:
        An instance of AuthService for token generation and password hashing.
    """
    return AuthService()

@pytest.fixture
async def mqtt_client_connected():
    """
    Provides a connected mock MQTT client for use in integration tests.
    
    Returns:
        A connected instance of MockMQTTClient.
    """
    client = MockMQTTClient()
    await client.connect()
    return client

@pytest.fixture
async def admin_user(db_session: AsyncSession, auth_service: AuthService):
    """
    Creates and persists an admin user in the test database for use in authenticated test scenarios.
    
    Returns:
        The created admin user model instance.
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
async def auth_headers(admin_user, auth_service: AuthService):
    """
    Generates authentication headers with a bearer token for the given admin user.
    
    Returns:
        A dictionary containing the Authorization header for authenticated API requests.
    """
    token_pair = auth_service.generate_token_pair(
        user_id=str(admin_user.id),
        email=admin_user.email,
        roles=admin_user.roles
    )
    return {"Authorization": f"Bearer {token_pair.access_token}"}

@pytest.fixture
async def test_data(db_session: AsyncSession):
    """
    Seeds the database with comprehensive test data for access control integration tests.
    
    Returns:
        The result of the seeding operation, typically including created users, cards, doors, and permissions for use in integration tests.
    """
    seeder = IntegrationSeeder(db_session)
    return await seeder.seed_complete_access_flow_data()

class TestCompleteAccessFlow:
    """Integration tests for complete access control workflow."""
    
    async def test_complete_successful_access_flow(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        test_data: dict,
        mqtt_client_connected
    ):
        """
        Tests a complete successful access validation flow for a regular user.
        
        Simulates an access validation request for a user with a standard card at a low-security door, asserting that access is granted, the response contains correct user and door information, and an MQTT event is published.
        """
        # Extract data from seeder
        user = test_data['regular_user']
        doors = test_data['doors']
        cards = test_data['cards']
        
        office_door = doors['low_security']  # Low security door
        user_card = cards['user_standard']  # User standard card
        
        # Test access validation using seeded data
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": user_card.card_id, "door_id": str(office_door.id)}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
        assert data["door_name"] == office_door.name
        assert data["user_name"] == user.full_name
        assert "Access granted" in data["reason"]
        
        # Verify MQTT message was published
        mqtt_client_connected.assert_topic_published(f"access/doors/{office_door.id}/events")

    async def test_master_card_access_flow(
        self,
        client: AsyncClient,
        test_doors: list[DoorModel],
        test_cards: list[CardModel],
        mqtt_client_connected
    ):
        """
        Tests that a master card grants access to a high-security door without explicit permission.
        
        Asserts that access is granted with the correct card type and reason, and verifies that an MQTT event is published for the door.
        """
        doors = test_doors
        cards = test_cards
        
        server_door = doors[1]  # High security server room
        master_card = cards[2]  # Master card
        
        # Master card should have access without explicit permission
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": master_card.card_id, "door_id": str(server_door.id)}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
        assert data["card_type"] == "master"
        assert "Master card access granted" in data["reason"]
        
        # Verify MQTT message was published
        mqtt_client_connected.assert_topic_published(f"access/doors/{server_door.id}/events")

    async def test_suspended_card_access_denied(
        self,
        client: AsyncClient,
        test_doors: list[DoorModel],
        test_cards: list[CardModel]
    ):
        """
        Tests that access is denied when a suspended card is used for validation.
        
        Sends an access validation request with a suspended card and verifies that the response status is 403 Forbidden, access is not granted, and the denial reason indicates card suspension.
        """
        doors = test_doors
        cards = test_cards
        
        office_door = doors[0]  # Office door
        suspended_card = cards[1]  # Suspended card
        
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": suspended_card.card_id, "door_id": str(office_door.id)}
        )
        
        assert response.status_code == 403
        data = response.json()
        assert data["access_granted"] is False
        assert "Card is suspended" in data["reason"]

    async def test_maintenance_door_access_denied(
        self,
        client: AsyncClient,
        test_doors: list[DoorModel],
        test_cards: list[CardModel]
    ):
        """
        Tests that access is denied when attempting to use an active card on a door marked as under maintenance.
        
        Asserts that the API returns HTTP 403, access is not granted, and the denial reason indicates maintenance status.
        """
        doors = test_doors
        cards = test_cards
        
        maintenance_door = doors[2]  # Maintenance door
        active_card = cards[0]  # Active card
        
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": active_card.card_id, "door_id": str(maintenance_door.id)}
        )
        
        assert response.status_code == 403
        data = response.json()
        assert data["access_granted"] is False
        assert "Door is under maintenance" in data["reason"]

    async def test_no_permission_access_denied(
        self,
        client: AsyncClient,
        test_doors: list[DoorModel],
        test_cards: list[CardModel]
    ):
        """
        Verifies that access is denied when a user lacks permission for a specific door.
        
        Sends an access validation request for a user without the required permission and asserts that the response is HTTP 403 with an appropriate denial reason.
        """
        doors = test_doors
        cards = test_cards
        
        server_door = doors[1]  # High security server room
        active_card = cards[0]  # Active card
        
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": active_card.card_id, "door_id": str(server_door.id)}
        )
        
        assert response.status_code == 403
        data = response.json()
        assert data["access_granted"] is False
        assert "No permission" in data["reason"]

    async def test_card_management_integration(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_employee_user: UserModel,
        db_session: AsyncSession
    ):
        """
        Tests the card management API endpoints for creating and retrieving a card.
        
        Creates a new card for an employee user via the API and verifies the response. Then retrieves the created card by its ID and asserts that the returned data matches the expected user and card information.
        """
        employee_user = test_employee_user
        headers = auth_headers
        
        # Create new card
        new_card_data = {
            "user_id": str(employee_user.id),
            "card_id": "NEW001",
            "card_type": "employee",
            "status": "active"
        }
        
        response = await client.post(
            "/api/v1/cards",
            headers=headers,
            json=new_card_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["card_id"] == "NEW001"
        assert data["status"] == "active"
        
        # Get card details
        response = await client.get(
            f"/api/v1/cards/{data['id']}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["card_id"] == "NEW001"
        assert data["user_id"] == str(employee_user.id)

    async def test_door_management_integration(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """
        Tests the door management API endpoints for creation and retrieval.
        
        Creates a new door using the API and verifies the response data, then retrieves the created door by ID and asserts the returned details match the input.
        """
        headers = auth_headers
        
        # Create new door
        new_door_data = {
            "name": "Test Door",
            "location": "Test Location",
            "security_level": "medium",
            "status": "active"
        }
        
        response = await client.post(
            "/api/v1/doors",
            headers=headers,
            json=new_door_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Door"
        assert data["security_level"] == "medium"
        
        # Get door details
        response = await client.get(
            f"/api/v1/doors/{data['id']}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Door"
        assert data["location"] == "Test Location"

    async def test_authentication_required_for_management(
        self,
        client: AsyncClient
    ):
        """
        Verifies that card and door management API endpoints reject unauthenticated requests.
        
        Sends POST requests to create cards and doors without authentication headers and asserts that both endpoints return HTTP 401 Unauthorized.
        """
        # Try to create a card without auth
        response = await client.post(
            "/api/v1/cards",
            json={
                "card_id": "TEST001",
                "card_type": "employee",
                "status": "active"
            }
        )
        
        assert response.status_code == 401
        
        # Try to create a door without auth
        response = await client.post(
            "/api/v1/doors",
            json={
                "name": "Test Door",
                "location": "Test Location",
                "security_level": "medium"
            }
        )
        
        assert response.status_code == 401

    async def test_invalid_data_validation(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """
        Tests that the API returns validation errors for invalid card and door data.
        
        Sends requests with invalid fields to the card and door creation endpoints and asserts that the responses have HTTP 422 status codes.
        """
        headers = auth_headers
        
        # Invalid card data
        response = await client.post(
            "/api/v1/cards",
            headers=headers,
            json={
                "card_id": "",  # Invalid empty card_id
                "card_type": "invalid_type",  # Invalid card type
                "status": "invalid_status"  # Invalid status
            }
        )
        
        assert response.status_code == 422
        
        # Invalid door data
        response = await client.post(
            "/api/v1/doors",
            headers=headers,
            json={
                "name": "",  # Invalid empty name
                "security_level": "invalid_level",  # Invalid security level
                "status": "invalid_status"  # Invalid status
            }
        )
        
        assert response.status_code == 422

    async def test_concurrent_access_validation(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_employee_user: UserModel,
        test_doors: list[DoorModel],
        test_cards: list[CardModel]
    ):
        """
        Tests that multiple concurrent access validation requests for a user with valid permission all succeed.
        
        Creates an active permission for the user and sends five simultaneous access validation requests to the API, asserting that each response grants access.
        """
        import asyncio
        employee_user = test_employee_user
        doors = test_doors
        cards = test_cards
        
        office_door = doors[0]
        active_card = cards[0]
        
        # Create permission
        permission = PermissionModel(
            user_id=employee_user.id,
            door_id=office_door.id,
            card_number=active_card.card_id,
            status="active",
            valid_from=time(8, 0),
            valid_until=time(18, 0),
            days_of_week=["mon", "tue", "wed", "thu", "fri"],
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(permission)
        await db_session.commit()
        
        # Make concurrent requests
        async def make_request():
            """
            Sends an asynchronous POST request to validate access for a specific card and door.
            
            Returns:
                The HTTP response from the access validation endpoint.
            """
            return await client.post(
                "/api/v1/access/validate",
                json={"card_id": active_card.card_id, "door_id": str(office_door.id)}
            )
        
        # Make 5 concurrent requests
        responses = await asyncio.gather(*[make_request() for _ in range(5)])
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["access_granted"] is True

    async def test_health_and_metrics_endpoints(
        self,
        client: AsyncClient
    ):
        """
        Verifies that the health check and metrics API endpoints return expected status and data.
        
        Sends requests to the health and metrics endpoints, asserting HTTP 200 responses and validating the presence of expected keys in the returned JSON.
        """
        # Health check
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        
        # Metrics
        response = await client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "successful_requests" in data
        assert "failed_requests" in data

    async def test_api_documentation_endpoints(
        self,
        client: AsyncClient
    ):
        """
        Verifies that the OpenAPI JSON and Swagger UI documentation endpoints are accessible and return the expected content.
        
        Asserts that the OpenAPI endpoint returns a valid specification with required keys, and that the Swagger UI endpoint serves HTML content.
        """
        # OpenAPI JSON
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
        
        # Swagger UI
        response = await client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]