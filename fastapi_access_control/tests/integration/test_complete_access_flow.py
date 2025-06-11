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
from app.shared.database.session import get_db
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.models.card import CardModel
from app.infrastructure.database.models.door import DoorModel
from app.infrastructure.database.models.permission import PermissionModel
from app.domain.services.auth_service import AuthService


class TestCompleteAccessFlow:
    """Integration tests for complete access control workflow."""
    
    @pytest.fixture
    async def client(self):
        """HTTP client for testing."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.fixture
    async def db_session(self):
        """Database session for testing."""
        async for session in get_db():
            yield session
            break
    
    @pytest.fixture
    async def auth_service(self):
        """Auth service for token generation."""
        return AuthService()
    
    @pytest.fixture
    async def admin_user(self, db_session: AsyncSession, auth_service: AuthService):
        """Create admin user for authenticated requests."""
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
    async def auth_headers(self, admin_user, auth_service: AuthService):
        """Authentication headers for API requests."""
        token_pair = auth_service.generate_token_pair(
            user_id=str(admin_user.id),
            email=admin_user.email,
            roles=admin_user.roles
        )
        return {"Authorization": f"Bearer {token_pair.access_token}"}
    
    @pytest.fixture
    async def test_employee_user(self, db_session: AsyncSession):
        """Create employee user for access testing."""
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
    async def test_doors(self, db_session: AsyncSession):
        """Create test doors with different security levels."""
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
    async def test_cards(self, db_session: AsyncSession, test_employee_user):
        """Create test cards for different scenarios."""
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
    
    @pytest.mark.asyncio
    async def test_complete_successful_access_flow(self, client: AsyncClient, db_session: AsyncSession, 
                                                    test_employee_user, test_doors, test_cards):
        """Test complete successful access validation flow."""
        office_door = test_doors[0]  # Office door (low security)
        active_card = test_cards[0]  # Active employee card
        
        # Create permission for user to access office door
        permission = PermissionModel(
            user_id=test_employee_user.id,
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
        
        # Test access validation
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": active_card.card_id, "door_id": office_door.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
        assert data["door_name"] == "Office Door"
        assert data["user_name"] == "Employee User"
        assert data["card_type"] == "employee"
        assert "Access granted" in data["reason"]
    
    @pytest.mark.asyncio
    async def test_master_card_access_flow(self, client: AsyncClient, test_doors, test_cards):
        """Test master card access to any door."""
        server_door = test_doors[1]  # High security server room
        master_card = test_cards[2]  # Master card
        
        # Master card should have access without explicit permission
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": master_card.card_id, "door_id": server_door.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
        assert data["card_type"] == "master"
        assert "Master card access granted" in data["reason"]
    
    @pytest.mark.asyncio
    async def test_suspended_card_access_denied(self, client: AsyncClient, test_doors, test_cards):
        """Test that suspended cards are denied access."""
        office_door = test_doors[0]
        suspended_card = test_cards[1]  # Suspended card
        
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": suspended_card.card_id, "door_id": office_door.id}
        )
        
        assert response.status_code == 400
        assert "inactive" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_maintenance_door_access_denied(self, client: AsyncClient, test_doors, test_cards):
        """Test that maintenance doors deny access."""
        maintenance_door = test_doors[2]  # Door in maintenance
        active_card = test_cards[0]
        
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": active_card.card_id, "door_id": maintenance_door.id}
        )
        
        assert response.status_code == 400
        assert "not accessible" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_no_permission_access_denied(self, client: AsyncClient, test_doors, test_cards):
        """Test access denied when user has no permission."""
        server_door = test_doors[1]  # Server room
        active_card = test_cards[0]  # Employee card (no permission for server room)
        
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": active_card.card_id, "door_id": server_door.id}
        )
        
        assert response.status_code == 403
        assert "does not have permission" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_card_management_integration(self, client: AsyncClient, auth_headers, 
                                                test_employee_user, db_session: AsyncSession):
        """Test complete card management flow via API."""
        # Create new card via API
        card_data = {
            "card_number": "NEW001",
            "user_id": test_employee_user.id,
            "card_type": "employee",
            "is_active": True
        }
        
        response = await client.post(
            "/api/v1/cards/",
            json=card_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        created_card = response.json()
        card_id = created_card["id"]
        
        # Get card details
        response = await client.get(f"/api/v1/cards/{card_id}", headers=auth_headers)
        assert response.status_code == 200
        card_details = response.json()
        assert card_details["card_number"] == "NEW001"
        
        # Update card
        update_data = {"card_type": "contractor"}
        response = await client.put(
            f"/api/v1/cards/{card_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Suspend card
        response = await client.post(f"/api/v1/cards/{card_id}/suspend", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify card is suspended
        response = await client.get(f"/api/v1/cards/{card_id}", headers=auth_headers)
        updated_card = response.json()
        assert updated_card["status"] == "suspended"
    
    @pytest.mark.asyncio
    async def test_door_management_integration(self, client: AsyncClient, auth_headers):
        """Test complete door management flow via API."""
        # Create new door via API
        door_data = {
            "name": "Conference Room A",
            "location": "Building B - Floor 2",
            "security_level": "medium",
            "description": "Main conference room"
        }
        
        response = await client.post(
            "/api/v1/doors/",
            json=door_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        created_door = response.json()
        door_id = created_door["id"]
        
        # Get door details
        response = await client.get(f"/api/v1/doors/{door_id}", headers=auth_headers)
        assert response.status_code == 200
        door_details = response.json()
        assert door_details["name"] == "Conference Room A"
        
        # Update door
        update_data = {"security_level": "high"}
        response = await client.put(
            f"/api/v1/doors/{door_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Set door to maintenance
        response = await client.post(
            f"/api/v1/doors/{door_id}/status",
            json={"status": "maintenance"},
            headers=auth_headers
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_authentication_required_for_management(self, client: AsyncClient, test_doors):
        """Test that management endpoints require authentication."""
        # Try to access cards without auth
        response = await client.get("/api/v1/cards/")
        assert response.status_code == 401
        
        # Try to create door without auth
        door_data = {
            "name": "Test Door",
            "location": "Test Location",
            "security_level": "low"
        }
        response = await client.post("/api/v1/doors/", json=door_data)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_invalid_data_validation(self, client: AsyncClient):
        """Test API validation for invalid data."""
        # Invalid card_id (empty)
        TEST_DOOR_ID = UUID("12345678-1234-5678-1234-567812345678")  # Example door ID
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": "", "door_id": TEST_DOOR_ID}
        )
        assert response.status_code == 422
        
        # Invalid door_id (negative)
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": "TEST123", "door_id": -1}
        )
        assert response.status_code == 422
        
        # Missing required fields
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": "TEST123"}
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_concurrent_access_validation(self, client: AsyncClient, db_session: AsyncSession,
                                                 test_employee_user, test_doors, test_cards):
        """Test concurrent access validation requests."""
        import asyncio
        
        office_door = test_doors[0]
        active_card = test_cards[0]
        
        # Create permission
        permission = PermissionModel(
            user_id=test_employee_user.id,
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
        
        # Make 5 concurrent requests
        async def make_request():
            return await client.post(
                "/api/v1/access/validate",
                json={"card_id": active_card.card_id, "door_id": office_door.id}
            )
        
        tasks = [make_request() for _ in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["access_granted"] is True
    
    @pytest.mark.asyncio
    async def test_health_and_metrics_endpoints(self, client: AsyncClient):
        """Test system health and metrics endpoints."""
        # Health check
        response = await client.get("/health")
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["status"] == "healthy"
        assert "timestamp" in health_data
        
        # Metrics endpoint
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "prometheus" in response.headers.get("content-type", "").lower() or \
               "text/plain" in response.headers.get("content-type", "")
    
    @pytest.mark.asyncio
    async def test_api_documentation_endpoints(self, client: AsyncClient):
        """Test API documentation is accessible."""
        # OpenAPI schema
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        openapi_data = response.json()
        assert "openapi" in openapi_data
        assert "paths" in openapi_data
        
        # Swagger UI
        response = await client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        
        # ReDoc
        response = await client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")