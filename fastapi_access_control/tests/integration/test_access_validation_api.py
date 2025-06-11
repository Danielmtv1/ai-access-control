"""
Integration tests for access validation API.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, time
from uuid import UUID

from app.main import app
from app.shared.database.session import get_db
from app.domain.entities.card import Card, CardType, CardStatus
from app.domain.entities.door import Door, DoorStatus, SecurityLevel
from app.domain.entities.user import User, Role, UserStatus
from app.domain.entities.permission import Permission, PermissionStatus
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.models.card import CardModel
from app.infrastructure.database.models.door import DoorModel
from app.infrastructure.database.models.permission import PermissionModel


class TestAccessValidationAPI:
    """Integration tests for access validation API."""
    
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
    async def test_user(self, db_session: AsyncSession):
        """Create test user in database."""
        user_model = UserModel(
            email="test@company.com",
            hashed_password="hashed_password",
            full_name="Test User",
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
    async def test_door(self, db_session: AsyncSession):
        """Create test door in database."""
        door_model = DoorModel(
            name="Test Door",
            location="Test Building",
            security_level="medium",
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(door_model)
        await db_session.commit()
        await db_session.refresh(door_model)
        return door_model
    
    @pytest.fixture
    async def test_card(self, db_session: AsyncSession, test_user):
        """Create test card in database."""
        card_model = CardModel(
            user_id=test_user.id,
            card_id="TEST123",
            card_type="employee",
            status="active",
            valid_from=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(card_model)
        await db_session.commit()
        await db_session.refresh(card_model)
        return card_model
    
    @pytest.fixture
    async def test_permission(self, db_session: AsyncSession, test_user, test_door, test_card):
        """Create test permission in database."""
        permission_model = PermissionModel(
            user_id=test_user.id,
            door_id=test_door.id,
            card_number=test_card.card_id,
            status="active",
            valid_from=time(8, 0),
            valid_until=time(18, 0),
            days_of_week=["mon", "tue", "wed", "thu", "fri"],
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(permission_model)
        await db_session.commit()
        await db_session.refresh(permission_model)
        return permission_model
    
    @pytest.mark.asyncio
    async def test_validate_access_card_not_found(self, client: AsyncClient):
        """Test access validation with non-existent card."""
        TEST_DOOR_ID = UUID('19932f0f-8063-4c82-9407-1d9e148f5738')   # Assuming a door with UUID  exists for testing
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": "NONEXISTENT", "door_id": TEST_DOOR_ID}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_validate_access_door_not_found(self, client: AsyncClient, test_card):
        """Test access validation with non-existent door."""
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": test_card.card_id, "door_id": 99999}
        )
        
        assert response.status_code == 404
        assert "Door 99999 not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_validate_access_no_permission(self, client: AsyncClient, test_card, test_door):
        """Test access validation when user has no permission."""
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": test_card.card_id, "door_id": test_door.id}
        )
        
        assert response.status_code == 403
        assert "does not have permission" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_validate_access_success(self, client: AsyncClient, test_card, test_door, test_permission):
        """Test successful access validation."""
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": test_card.card_id, "door_id": test_door.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
        assert data["door_name"] == "Test Door"
        assert data["user_name"] == "Test User"
        assert data["card_type"] == "employee"
        assert "Access granted" in data["reason"]
    
    @pytest.mark.asyncio
    async def test_validate_access_invalid_request_format(self, client: AsyncClient):
        """Test access validation with invalid request format."""
        response = await client.post(
            "/api/v1/access/validate",
            json={"invalid": "data"}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_validate_access_master_card(self, client: AsyncClient, test_door, test_user, db_session: AsyncSession):
        """Test access validation with master card."""
        # Create master card
        master_card = CardModel(
            user_id=test_user.id,
            card_id="MASTER123",
            card_type="master",
            status="active",
            valid_from=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(master_card)
        await db_session.commit()
        
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": "MASTER123", "door_id": test_door.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
        assert data["card_type"] == "master"
        assert "Master card access granted" in data["reason"]
    
    @pytest.mark.asyncio
    async def test_validate_access_with_pin(self, client: AsyncClient, test_card, test_door, test_permission):
        """Test access validation with PIN."""
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": test_card.card_id, "door_id": test_door.id, "pin": "1234"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
    
    @pytest.mark.asyncio
    async def test_validate_access_suspended_card(self, client: AsyncClient, test_card, test_door, db_session: AsyncSession):
        """Test access validation with suspended card."""
        # Suspend the card
        test_card.status = "suspended"
        await db_session.commit()
        
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": test_card.card_id, "door_id": test_door.id}
        )
        
        assert response.status_code == 400
        assert "inactive" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_validate_access_inactive_door(self, client: AsyncClient, test_card, test_door, db_session: AsyncSession):
        """Test access validation with inactive door."""
        # Deactivate the door
        test_door.status = "maintenance"
        await db_session.commit()
        
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": test_card.card_id, "door_id": test_door.id}
        )
        
        assert response.status_code == 400
        assert "not accessible" in response.json()["detail"]