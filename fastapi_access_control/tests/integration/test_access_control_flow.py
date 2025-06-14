import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, UTC, timedelta, time
from app.domain.entities.card import Card, CardType, CardStatus
from app.domain.entities.door import Door, DoorType, SecurityLevel, DoorStatus, AccessSchedule
from app.domain.entities.user import User, Role, UserStatus
from app.domain.services.auth_service import AuthService
from tests.conftest import SAMPLE_USER_UUID, SAMPLE_CARD_UUID, SAMPLE_CARD_UUID_2, SAMPLE_DOOR_UUID, SAMPLE_DOOR_UUID_2, SAMPLE_ADMIN_UUID

class TestAccessControlFlow:
    """Integration tests for complete access control flow scenarios"""
    
    @pytest.fixture
    def auth_service(self):
        """Local auth service instance"""
        return AuthService()
    
    @pytest.fixture
    def sample_admin_user(self):
        """Sample admin user for testing"""
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
    def admin_jwt_token(self, auth_service, sample_admin_user):
        """Valid JWT token for admin user"""
        return auth_service.generate_access_token(sample_admin_user)
    
    @pytest.fixture
    def admin_headers(self, admin_jwt_token):
        """Headers with admin JWT token"""
        return {"Authorization": f"Bearer {admin_jwt_token}"}
    
    @pytest.fixture
    def sync_client(self):
        """Synchronous test client for these specific tests"""
        from app.main import app
        from app.api.dependencies.auth_dependencies import get_current_user
        
        # Mock the auth dependency to skip authentication for these tests
        def mock_get_current_user():
            from app.domain.entities.user import User, Role, UserStatus
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
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        client = TestClient(app)
        
        yield client
        
        # Clean up override
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
    
    @pytest.fixture
    def auth_client(self):
        """Synchronous test client WITHOUT auth bypass for auth flow testing"""
        from app.main import app
        return TestClient(app)
    
    def test_complete_card_management_flow(self, sync_client: TestClient, admin_headers):
        """Test complete card management workflow: create, read, update, suspend, delete"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        # Step 1: Create a new card
        with patch('app.api.v1.cards.CreateCardUseCase') as mock_create_use_case:
            mock_create = AsyncMock()
            mock_create_use_case.return_value = mock_create
            
            created_card = Card(
                id=SAMPLE_CARD_UUID,
                card_id="EMPLOYEE001",
                user_id=SAMPLE_USER_UUID,
                card_type=CardType.EMPLOYEE,
                status=CardStatus.ACTIVE,
                valid_from=now,
                valid_until=now + timedelta(days=365),
                created_at=now,
                updated_at=now,
                use_count=0
            )
            mock_create.execute.return_value = created_card
            
            card_data = {
                "card_id": "EMPLOYEE001",
                "user_id": str(SAMPLE_USER_UUID),
                "card_type": "employee",
                "valid_from": now.isoformat(),
                "valid_until": (now + timedelta(days=365)).isoformat()
            }
            
            response = sync_client.post("/api/v1/cards/", json=card_data, headers=admin_headers)
            assert response.status_code == 201
            assert response.json()["card_id"] == "EMPLOYEE001"
        
        # Step 2: Retrieve the card by card_id
        with patch('app.api.v1.cards.GetCardByCardIdUseCase') as mock_get_use_case:
            mock_get = AsyncMock()
            mock_get_use_case.return_value = mock_get
            mock_get.execute.return_value = created_card
            
            response = sync_client.get("/api/v1/cards/by-card-id/EMPLOYEE001", headers=admin_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["card_id"] == "EMPLOYEE001"
            assert data["status"] == "active"
        
        # Step 3: Update the card to visitor type
        with patch('app.api.v1.cards.UpdateCardUseCase') as mock_update_use_case:
            mock_update = AsyncMock()
            mock_update_use_case.return_value = mock_update
            
            updated_card = Card(
                id=SAMPLE_CARD_UUID,
                card_id="EMPLOYEE001",
                user_id=SAMPLE_USER_UUID,
                card_type=CardType.VISITOR,  # Updated
                status=CardStatus.ACTIVE,
                valid_from=now,
                valid_until=now + timedelta(days=30),  # Updated
                created_at=now,
                updated_at=now + timedelta(minutes=5),
                use_count=0
            )
            mock_update.execute.return_value = updated_card
            
            update_data = {
                "card_type": "visitor",
                "valid_until": (now + timedelta(days=30)).isoformat()
            }
            
            response = sync_client.put(f"/api/v1/cards/{SAMPLE_CARD_UUID}", json=update_data, headers=admin_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["card_type"] == "visitor"
        
        # Step 4: Suspend the card
        with patch('app.api.v1.cards.SuspendCardUseCase') as mock_suspend_use_case:
            mock_suspend = AsyncMock()
            mock_suspend_use_case.return_value = mock_suspend
            
            suspended_card = Card(
                id=SAMPLE_CARD_UUID,
                card_id="EMPLOYEE001",
                user_id=SAMPLE_USER_UUID,
                card_type=CardType.VISITOR,
                status=CardStatus.SUSPENDED,  # Updated
                valid_from=now,
                valid_until=now + timedelta(days=30),
                created_at=now,
                updated_at=now + timedelta(minutes=10),
                use_count=0
            )
            mock_suspend.execute.return_value = suspended_card
            
            response = sync_client.post(f"/api/v1/cards/{SAMPLE_CARD_UUID}/suspend", headers=admin_headers)
            assert response.status_code == 200
            assert response.json()["status"] == "suspended"
        
        # Step 5: Delete the card
        with patch('app.api.v1.cards.DeleteCardUseCase') as mock_delete_use_case:
            mock_delete = AsyncMock()
            mock_delete_use_case.return_value = mock_delete
            mock_delete.execute.return_value = True
            
            response = sync_client.delete(f"/api/v1/cards/{SAMPLE_CARD_UUID}", headers=admin_headers)
            assert response.status_code == 204
    
    def test_complete_door_management_flow(self, sync_client: TestClient, admin_headers):
        """Test complete door management workflow: create, read, update status, delete"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        # Step 1: Create a new door with schedule
        with patch('app.api.v1.doors.CreateDoorUseCase') as mock_create_use_case:
            mock_create = AsyncMock()
            mock_create_use_case.return_value = mock_create
            
            schedule = AccessSchedule(
                days_of_week=[0, 1, 2, 3, 4],
                start_time=time(9, 0),
                end_time=time(17, 0)
            )
            created_door = Door(
                id=SAMPLE_DOOR_UUID,
                name="Conference Room A",
                location="Building A - Floor 2",
                door_type=DoorType.ENTRANCE,
                security_level=SecurityLevel.MEDIUM,
                status=DoorStatus.ACTIVE,
                created_at=now,
                updated_at=now,
                description="Conference room access",
                default_schedule=schedule,
                requires_pin=True,
                max_attempts=3,
                lockout_duration=300,
                failed_attempts=0
            )
            mock_create.execute.return_value = created_door
            
            door_data = {
                "name": "Conference Room A",
                "location": "Building A - Floor 2",
                "description": "Conference room access",
                "door_type": "entrance",
                "security_level": "medium",
                "requires_pin": True,
                "max_attempts": 3,
                "lockout_duration": 300,
                "default_schedule": {
                    "days_of_week": [0, 1, 2, 3, 4],
                    "start_time": "09:00",
                    "end_time": "17:00"
                }
            }
            
            response = sync_client.post("/api/v1/doors/", json=door_data, headers=admin_headers)
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Conference Room A"
            assert data["requires_pin"] is True
        
        # Step 2: Retrieve door by name
        with patch('app.api.v1.doors.GetDoorByNameUseCase') as mock_get_use_case:
            mock_get = AsyncMock()
            mock_get_use_case.return_value = mock_get
            mock_get.execute.return_value = created_door
            
            response = sync_client.get("/api/v1/doors/by-name/Conference Room A", headers=admin_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Conference Room A"
            assert data["security_level"] == "medium"
        
        # Step 3: Update door to high security
        with patch('app.api.v1.doors.UpdateDoorUseCase') as mock_update_use_case:
            mock_update = AsyncMock()
            mock_update_use_case.return_value = mock_update
            
            updated_door = Door(
                id=SAMPLE_DOOR_UUID,
                name="Conference Room A",
                location="Building A - Floor 2",
                door_type=DoorType.ENTRANCE,
                security_level=SecurityLevel.HIGH,  # Updated
                status=DoorStatus.ACTIVE,
                created_at=now,
                updated_at=now + timedelta(minutes=5),
                description="High security conference room",  # Updated
                default_schedule=schedule,
                requires_pin=True,
                max_attempts=2,  # Updated
                lockout_duration=600,  # Updated
                failed_attempts=0
            )
            mock_update.execute.return_value = updated_door
            
            update_data = {
                "security_level": "high",
                "description": "High security conference room",
                "max_attempts": 2,
                "lockout_duration": 600
            }
            
            response = sync_client.put(f"/api/v1/doors/{SAMPLE_DOOR_UUID}", json=update_data, headers=admin_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["security_level"] == "high"
            assert data["max_attempts"] == 2
        
        # Step 4: Set door to maintenance mode
        with patch('app.api.v1.doors.SetDoorStatusUseCase') as mock_status_use_case:
            mock_status = AsyncMock()
            mock_status_use_case.return_value = mock_status
            
            maintenance_door = Door(
                id=SAMPLE_DOOR_UUID,
                name="Conference Room A",
                location="Building A - Floor 2",
                door_type=DoorType.ENTRANCE,
                security_level=SecurityLevel.HIGH,
                status=DoorStatus.MAINTENANCE,  # Updated
                created_at=now,
                updated_at=now + timedelta(minutes=10),
                description="High security conference room",
                default_schedule=schedule,
                requires_pin=True,
                max_attempts=2,
                lockout_duration=600,
                failed_attempts=0
            )
            mock_status.execute.return_value = maintenance_door
            
            status_data = {"status": "maintenance"}
            response = sync_client.post(f"/api/v1/doors/{SAMPLE_DOOR_UUID}/status", json=status_data, headers=admin_headers)
            assert response.status_code == 200
            assert response.json()["status"] == "maintenance"
        
        # Step 5: Get doors by security level
        with patch('app.api.v1.doors.GetDoorsBySecurityLevelUseCase') as mock_security_use_case:
            mock_security = AsyncMock()
            mock_security_use_case.return_value = mock_security
            mock_security.execute.return_value = [maintenance_door]
            
            response = sync_client.get("/api/v1/doors/security-level/high", headers=admin_headers)
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["security_level"] == "high"
        
        # Step 6: Delete the door
        with patch('app.api.v1.doors.DeleteDoorUseCase') as mock_delete_use_case:
            mock_delete = AsyncMock()
            mock_delete_use_case.return_value = mock_delete
            mock_delete.execute.return_value = True
            
            response = sync_client.delete(f"/api/v1/doors/{SAMPLE_DOOR_UUID}", headers=admin_headers)
            assert response.status_code == 204
    
    def test_user_card_association_flow(self, sync_client: TestClient, admin_headers):
        """Test flow of associating multiple cards with a user"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        # Step 1: Create primary employee card
        with patch('app.api.v1.cards.CreateCardUseCase') as mock_create_use_case:
            mock_create = AsyncMock()
            mock_create_use_case.return_value = mock_create
            
            primary_card = Card(
                id=SAMPLE_CARD_UUID,
                card_id="EMP001_PRIMARY",
                user_id=SAMPLE_USER_UUID,
                card_type=CardType.EMPLOYEE,
                status=CardStatus.ACTIVE,
                valid_from=now,
                valid_until=None,  # Permanent card
                created_at=now,
                updated_at=now,
                use_count=0
            )
            mock_create.execute.return_value = primary_card
            
            card_data = {
                "card_id": "EMP001_PRIMARY",
                "user_id": str(SAMPLE_USER_UUID),
                "card_type": "employee",
                "valid_from": now.isoformat()
            }
            
            response = sync_client.post("/api/v1/cards/", json=card_data, headers=admin_headers)
            assert response.status_code == 201
        
        # Step 2: Create backup card for same user
        with patch('app.api.v1.cards.CreateCardUseCase') as mock_create_use_case2:
            mock_create2 = AsyncMock()
            mock_create_use_case2.return_value = mock_create2
            
            backup_card = Card(
                id=SAMPLE_CARD_UUID_2,
                card_id="EMP001_BACKUP",
                user_id=SAMPLE_USER_UUID,
                card_type=CardType.EMPLOYEE,
                status=CardStatus.INACTIVE,  # Backup card starts inactive
                valid_from=now,
                valid_until=None,
                created_at=now,
                updated_at=now,
                use_count=0
            )
            mock_create2.execute.return_value = backup_card
            
            backup_data = {
                "card_id": "EMP001_BACKUP",
                "user_id": str(SAMPLE_USER_UUID),
                "card_type": "employee",
                "valid_from": now.isoformat()
            }
            
            response = sync_client.post("/api/v1/cards/", json=backup_data, headers=admin_headers)
            assert response.status_code == 201
        
        # Step 3: Create temporary visitor card for same user
        with patch('app.api.v1.cards.CreateCardUseCase') as mock_create_use_case3:
            mock_create3 = AsyncMock()
            mock_create_use_case3.return_value = mock_create3
            
            temp_card = Card(
                id=SAMPLE_CARD_UUID_2,
                card_id="VISITOR_TEMP_001",
                user_id=SAMPLE_USER_UUID,
                card_type=CardType.TEMPORARY,
                status=CardStatus.ACTIVE,
                valid_from=now,
                valid_until=now + timedelta(hours=8),  # 8-hour access
                created_at=now,
                updated_at=now,
                use_count=0
            )
            mock_create3.execute.return_value = temp_card
            
            temp_data = {
                "card_id": "VISITOR_TEMP_001",
                "user_id": str(SAMPLE_USER_UUID),
                "card_type": "temporary",
                "valid_from": now.isoformat(),
                "valid_until": (now + timedelta(hours=8)).isoformat()
            }
            
            response = sync_client.post("/api/v1/cards/", json=temp_data, headers=admin_headers)
            assert response.status_code == 201
        
        # Step 4: Get all cards for the user
        with patch('app.api.v1.cards.GetUserCardsUseCase') as mock_get_user_cards:
            mock_get = AsyncMock()
            mock_get_user_cards.return_value = mock_get
            mock_get.execute.return_value = [primary_card, backup_card, temp_card]
            
            response = sync_client.get(f"/api/v1/cards/user/{SAMPLE_USER_UUID}", headers=admin_headers)
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 3
            
            # Verify card types
            card_types = [card["card_type"] for card in data]
            assert "employee" in card_types
            assert "temporary" in card_types
            
            # Verify statuses
            card_statuses = [card["status"] for card in data]
            assert "active" in card_statuses
            assert "inactive" in card_statuses
    
    def test_door_location_filtering_flow(self, sync_client: TestClient, admin_headers):
        """Test flow of filtering doors by location and security level"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        # Step 1: Get doors by location
        with patch('app.api.v1.doors.GetDoorsByLocationUseCase') as mock_location_use_case:
            mock_location = AsyncMock()
            mock_location_use_case.return_value = mock_location
            
            building_a_doors = [
                Door(
                    id=SAMPLE_DOOR_UUID,
                    name="Main Lobby",
                    location="Building A",
                    door_type=DoorType.ENTRANCE,
                    security_level=SecurityLevel.LOW,
                    status=DoorStatus.ACTIVE,
                    created_at=now,
                    updated_at=now
                ),
                Door(
                    id=SAMPLE_DOOR_UUID_2,
                    name="Server Room",
                    location="Building A",
                    door_type=DoorType.ENTRANCE,
                    security_level=SecurityLevel.CRITICAL,
                    status=DoorStatus.ACTIVE,
                    created_at=now,
                    updated_at=now,
                    requires_pin=True
                )
            ]
            mock_location.execute.return_value = building_a_doors
            
            response = sync_client.get("/api/v1/doors/location/Building A", headers=admin_headers)
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert all(door["location"] == "Building A" for door in data)
        
        # Step 2: Get high security doors
        with patch('app.api.v1.doors.GetDoorsBySecurityLevelUseCase') as mock_security_use_case:
            mock_security = AsyncMock()
            mock_security_use_case.return_value = mock_security
            
            # Only the server room should be critical security
            critical_doors = [building_a_doors[1]]  # Server room only
            mock_security.execute.return_value = critical_doors
            
            response = sync_client.get("/api/v1/doors/security-level/critical", headers=admin_headers)
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "Server Room"
            assert data[0]["security_level"] == "critical"
            assert data[0]["requires_pin"] is True
        
        # Step 3: Get all active doors
        with patch('app.api.v1.doors.GetActiveDoorsUseCase') as mock_active_use_case:
            mock_active = AsyncMock()
            mock_active_use_case.return_value = mock_active
            mock_active.execute.return_value = building_a_doors
            
            response = sync_client.get("/api/v1/doors/?active_only=true", headers=admin_headers)
            assert response.status_code == 200
            data = response.json()
            assert all(door["status"] == "active" for door in data["doors"])
    
    def test_authentication_flow_integration(self, auth_client: TestClient):
        """Test authentication flow for API access"""
        # Step 1: Attempt access without authentication
        response = auth_client.get("/api/v1/cards/")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
        
        # Step 2: Login and get token
        with patch('app.api.v1.auth.AuthenticateUserUseCase') as mock_auth_use_case:
            mock_auth = AsyncMock()
            mock_auth_use_case.return_value = mock_auth
            
            # Create a valid token pair using auth service
            auth_service = AuthService()
            admin_user = User(
                id=SAMPLE_ADMIN_UUID,
                email="admin@access-control.com",
                hashed_password="$2b$12$admin.hash.here",
                full_name="Admin User",
                roles=[Role.ADMIN, Role.OPERATOR],
                status=UserStatus.ACTIVE,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            token_pair = auth_service.generate_token_pair(admin_user)
            mock_auth.execute.return_value = token_pair
            
            login_data = {
                "email": "admin@access-control.com",
                "password": "AdminPassword123!"
            }
            
            response = auth_client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            access_token = data["access_token"]
        
        # Step 3: Verify we got a valid token
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # For this test, we just verify the token format is valid
        # In a real integration test, we'd need the full auth infrastructure
        assert access_token is not None
        assert len(access_token) > 20  # JWT tokens are much longer
        assert "." in access_token  # JWT tokens have dots as separators