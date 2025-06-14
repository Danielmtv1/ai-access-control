import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, UTC, timedelta, time
from app.domain.entities.door import Door, DoorType, SecurityLevel, DoorStatus, AccessSchedule
from app.domain.entities.user import User, Role, UserStatus
from tests.conftest import SAMPLE_DOOR_UUID, SAMPLE_DOOR_UUID_2, SAMPLE_ADMIN_UUID

class TestDoorsAPI:
    """Integration tests for Doors API endpoints"""
    
    @pytest.fixture
    def client(self):
        """HTTP client for testing."""
        from app.main import app
        return TestClient(app)
    
    @pytest.fixture
    def mock_admin_user(self):
        """Mock admin user for testing."""
        return User(
            id=SAMPLE_ADMIN_UUID,
            email="admin@test.com",
            hashed_password="hashed_password",
            full_name="Admin User",
            roles=[Role.ADMIN],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
    
    def setup_auth_override(self, client, user):
        """Helper to setup authentication override."""
        from app.api.dependencies.auth_dependencies import get_current_active_user
        client.app.dependency_overrides[get_current_active_user] = lambda: user
        
    def cleanup_overrides(self, client):
        """Helper to cleanup dependency overrides."""
        client.app.dependency_overrides.clear()
    
    def test_create_door_success(self, client, mock_admin_user):
        """Test successful door creation"""
        # Create mocks
        mock_door_repository = AsyncMock()
        
        # Use FastAPI dependency override system
        from app.api.v1.doors import get_door_repository
        from app.api.dependencies.auth_dependencies import get_current_active_user
        
        client.app.dependency_overrides[get_door_repository] = lambda: mock_door_repository
        client.app.dependency_overrides[get_current_active_user] = lambda: mock_admin_user
        
        try:
            # Mock successful door creation
            now = datetime.now(UTC).replace(tzinfo=None)
            schedule = AccessSchedule(
                days_of_week=[0, 1, 2, 3, 4],
                start_time=time(9, 0),
                end_time=time(18, 0)
            )
            created_door = Door(
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
            # Mock repository methods
            mock_door_repository.get_by_name.return_value = None  # No existing door
            mock_door_repository.create.return_value = created_door
            
            # Make request
            door_data = {
                "name": "Main Entrance",
                "location": "Building A",
                "door_type": "entrance",
                "security_level": "medium",
                "description": "Main building entrance",
                "requires_pin": False,
                "max_attempts": 3,
                "lockout_duration": 300,
                "default_schedule": {
                    "days_of_week": [0, 1, 2, 3, 4],
                    "start_time": "09:00",
                    "end_time": "18:00"
                }
            }
            
            # Make request (no auth header needed since we override the dependency)
            response = client.post("/api/v1/doors/", json=door_data)
            
            # Verify response
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Main Entrance"
            assert data["location"] == "Building A"
            assert data["door_type"] == "entrance"
            assert data["security_level"] == "medium"
            assert data["status"] == "active"
            
        finally:
            # Clean up dependency overrides
            client.app.dependency_overrides.clear()

    def test_create_door_without_schedule(self, client, mock_admin_user):
        """Test door creation without default schedule"""
        # Create mocks
        mock_door_repository = AsyncMock()
        
        # Use FastAPI dependency override system
        from app.api.v1.doors import get_door_repository
        from app.api.dependencies.auth_dependencies import get_current_active_user
        
        client.app.dependency_overrides[get_door_repository] = lambda: mock_door_repository
        client.app.dependency_overrides[get_current_active_user] = lambda: mock_admin_user
        
        try:
            # Mock successful door creation without schedule
            now = datetime.now(UTC).replace(tzinfo=None)
            created_door = Door(
                id=SAMPLE_DOOR_UUID,
                name="Side Entrance",
                location="Building B",
                door_type=DoorType.ENTRANCE,
                security_level=SecurityLevel.LOW,
                status=DoorStatus.ACTIVE,
                created_at=now,
                updated_at=now,
                description="Side building entrance",
                default_schedule=None,
                requires_pin=False,
                max_attempts=3,
                lockout_duration=300,
                failed_attempts=0
            )
            
            # Mock repository methods
            mock_door_repository.get_by_name.return_value = None  # No existing door
            mock_door_repository.create.return_value = created_door
            
            # Make request without schedule
            door_data = {
                "name": "Side Entrance",
                "location": "Building B",
                "door_type": "entrance",
                "security_level": "low",
                "description": "Side building entrance"
            }
            
            response = client.post("/api/v1/doors/", json=door_data)
            
            # Verify response
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Side Entrance"
            assert data["default_schedule"] is None
            
        finally:
            # Clean up dependency overrides
            client.app.dependency_overrides.clear()

    def test_create_door_unauthorized(self, client):
        """Test door creation without authentication"""
        door_data = {
            "name": "Test Door",
            "location": "Building A",
            "door_type": "entrance",
            "security_level": "medium"
        }
        
        response = client.post("/api/v1/doors/", json=door_data)
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_create_door_validation_error(self, client, mock_admin_user):
        """Test door creation with invalid data"""
        # Setup authentication
        self.setup_auth_override(client, mock_admin_user)
        
        # Make request with invalid data
        door_data = {
            "name": "",  # Empty name should fail validation
            "location": "Building A",
            "door_type": "invalid_type",  # Invalid door type
            "security_level": "invalid_level"  # Invalid security level
        }
        
        try:
            response = client.post("/api/v1/doors/", json=door_data, headers={"Authorization": "Bearer fake_token"})
            
            # Verify validation error
            assert response.status_code == 422
        finally:
            self.cleanup_overrides(client)

    def test_get_door_success(self, client, mock_admin_user):
        """Test successful door retrieval"""
        # Create mocks
        mock_door_repository = AsyncMock()
        
        # Use FastAPI dependency override system
        from app.api.v1.doors import get_door_repository
        from app.api.dependencies.auth_dependencies import get_current_active_user
        
        client.app.dependency_overrides[get_door_repository] = lambda: mock_door_repository
        client.app.dependency_overrides[get_current_active_user] = lambda: mock_admin_user
        
        try:
            # Mock door retrieval
            now = datetime.now(UTC).replace(tzinfo=None)
            schedule = AccessSchedule(
                days_of_week=[0, 1, 2, 3, 4],
                start_time=time(9, 0),
                end_time=time(18, 0)
            )
            door = Door(
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
            mock_door_repository.get_by_id.return_value = door
            
            response = client.get(f"/api/v1/doors/{SAMPLE_DOOR_UUID}")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Main Entrance"
            assert data["id"] == str(SAMPLE_DOOR_UUID)
        finally:
            # Clean up dependency overrides
            client.app.dependency_overrides.clear()

    def test_get_door_not_found(self, client, mock_admin_user):
        """Test door retrieval when door doesn't exist"""
        # Create mocks
        mock_door_repository = AsyncMock()
        
        # Use FastAPI dependency override system
        from app.api.v1.doors import get_door_repository
        from app.api.dependencies.auth_dependencies import get_current_active_user
        
        client.app.dependency_overrides[get_door_repository] = lambda: mock_door_repository
        client.app.dependency_overrides[get_current_active_user] = lambda: mock_admin_user
        
        try:
            # Mock repository to return None (door not found)
            mock_door_repository.get_by_id.return_value = None
            
            response = client.get(f"/api/v1/doors/{SAMPLE_DOOR_UUID}")
            
            # Verify not found response
            assert response.status_code == 404
        finally:
            # Clean up dependency overrides
            client.app.dependency_overrides.clear()

    def test_get_door_by_name_success(self, client, mock_admin_user):
        """Test door retrieval by name"""
        # Create mocks
        mock_door_repository = AsyncMock()
        
        # Use FastAPI dependency override system
        from app.api.v1.doors import get_door_repository
        from app.api.dependencies.auth_dependencies import get_current_active_user
        
        client.app.dependency_overrides[get_door_repository] = lambda: mock_door_repository
        client.app.dependency_overrides[get_current_active_user] = lambda: mock_admin_user
        
        try:
            # Mock door retrieval
            now = datetime.now(UTC).replace(tzinfo=None)
            door = Door(
                id=SAMPLE_DOOR_UUID,
                name="Main Entrance",
                location="Building A",
                door_type=DoorType.ENTRANCE,
                security_level=SecurityLevel.MEDIUM,
                status=DoorStatus.ACTIVE,
                created_at=now,
                updated_at=now,
                description="Main building entrance",
                default_schedule=None,
                requires_pin=False,
                max_attempts=3,
                lockout_duration=300,
                failed_attempts=0
            )
            mock_door_repository.get_by_name.return_value = door
            
            response = client.get("/api/v1/doors/by-name/Main%20Entrance")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Main Entrance"
        finally:
            # Clean up dependency overrides
            client.app.dependency_overrides.clear()

    def test_get_doors_by_location_success(self, client, mock_admin_user):
        """Test door retrieval by location"""
        # Create mocks
        mock_door_repository = AsyncMock()
        
        # Use FastAPI dependency override system
        from app.api.v1.doors import get_door_repository
        from app.api.dependencies.auth_dependencies import get_current_active_user
        
        client.app.dependency_overrides[get_door_repository] = lambda: mock_door_repository
        client.app.dependency_overrides[get_current_active_user] = lambda: mock_admin_user
        
        try:
            # Mock doors retrieval
            now = datetime.now(UTC).replace(tzinfo=None)
            doors = [
                Door(
                    id=SAMPLE_DOOR_UUID,
                    name="Main Entrance",
                    location="Building A",
                    door_type=DoorType.ENTRANCE,
                    security_level=SecurityLevel.MEDIUM,
                    status=DoorStatus.ACTIVE,
                    created_at=now,
                    updated_at=now,
                    description="Main building entrance",
                    default_schedule=None,
                    requires_pin=False,
                    max_attempts=3,
                    lockout_duration=300,
                    failed_attempts=0
                )
            ]
            mock_door_repository.get_by_location.return_value = doors
            
            response = client.get("/api/v1/doors/location/Building%20A")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["location"] == "Building A"
        finally:
            # Clean up dependency overrides
            client.app.dependency_overrides.clear()

    def test_get_doors_by_security_level_success(self, client, mock_admin_user):
        """Test door retrieval by security level"""
        with patch('app.api.v1.doors.GetDoorsBySecurityLevelUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock doors retrieval
            now = datetime.now(UTC).replace(tzinfo=None)
            doors = [
                Door(
                    id=SAMPLE_DOOR_UUID,
                    name="Secure Door",
                    location="Building A",
                    door_type=DoorType.EMERGENCY,
                    security_level=SecurityLevel.HIGH,
                    status=DoorStatus.ACTIVE,
                    created_at=now,
                    updated_at=now,
                    description="High security door",
                    default_schedule=None,
                    requires_pin=True,
                    max_attempts=3,
                    lockout_duration=300,
                    failed_attempts=0
                )
            ]
            mock_use_case.execute.return_value = doors
            
            try:
                response = client.get("/api/v1/doors/security-level/high", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["security_level"] == "high"
            finally:
                self.cleanup_overrides(client)

    def test_list_doors_success(self, client, mock_admin_user):
        """Test listing all doors"""
        with patch('app.api.v1.doors.ListDoorsUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock doors retrieval
            now = datetime.now(UTC).replace(tzinfo=None)
            doors = [
                Door(
                    id=SAMPLE_DOOR_UUID,
                    name="Door 1",
                    location="Building A",
                    door_type=DoorType.ENTRANCE,
                    security_level=SecurityLevel.MEDIUM,
                    status=DoorStatus.ACTIVE,
                    created_at=now,
                    updated_at=now,
                    description="First door",
                    default_schedule=None,
                    requires_pin=False,
                    max_attempts=3,
                    lockout_duration=300,
                    failed_attempts=0
                ),
                Door(
                    id=SAMPLE_DOOR_UUID_2,
                    name="Door 2",
                    location="Building B",
                    door_type=DoorType.ENTRANCE,
                    security_level=SecurityLevel.LOW,
                    status=DoorStatus.ACTIVE,
                    created_at=now,
                    updated_at=now,
                    description="Second door",
                    default_schedule=None,
                    requires_pin=False,
                    max_attempts=3,
                    lockout_duration=300,
                    failed_attempts=0
                )
            ]
            mock_use_case.execute.return_value = doors
            
            try:
                response = client.get("/api/v1/doors/", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert len(data["doors"]) == 2  # Access doors array in DoorListResponse
            finally:
                self.cleanup_overrides(client)

    def test_list_doors_active_only(self, client, mock_admin_user):
        """Test listing only active doors"""
        with patch('app.api.v1.doors.GetActiveDoorsUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock active doors retrieval
            now = datetime.now(UTC).replace(tzinfo=None)
            doors = [
                Door(
                    id=SAMPLE_DOOR_UUID,
                    name="Active Door",
                    location="Building A",
                    door_type=DoorType.ENTRANCE,
                    security_level=SecurityLevel.MEDIUM,
                    status=DoorStatus.ACTIVE,
                    created_at=now,
                    updated_at=now,
                    description="Active door",
                    default_schedule=None,
                    requires_pin=False,
                    max_attempts=3,
                    lockout_duration=300,
                    failed_attempts=0
                )
            ]
            mock_use_case.execute.return_value = doors
            
            try:
                response = client.get("/api/v1/doors/?active_only=true", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert len(data["doors"]) == 1  # Access doors array in DoorListResponse
                assert data["doors"][0]["status"] == "active"
            finally:
                self.cleanup_overrides(client)

    def test_update_door_success(self, client, mock_admin_user):
        """Test successful door update"""
        with patch('app.api.v1.doors.UpdateDoorUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock updated door
            now = datetime.now(UTC).replace(tzinfo=None)
            updated_door = Door(
                id=SAMPLE_DOOR_UUID,
                name="Updated Door",
                location="Building A",
                door_type=DoorType.ENTRANCE,
                security_level=SecurityLevel.HIGH,
                status=DoorStatus.ACTIVE,
                created_at=now,
                updated_at=now,
                description="Updated description",
                default_schedule=None,
                requires_pin=True,
                max_attempts=5,
                lockout_duration=600,
                failed_attempts=0
            )
            mock_use_case.execute.return_value = updated_door
            
            update_data = {
                "name": "Updated Door",
                "security_level": "high",
                "description": "Updated description",
                "requires_pin": True,
                "max_attempts": 5,
                "lockout_duration": 600
            }
            
            try:
                response = client.put(f"/api/v1/doors/{SAMPLE_DOOR_UUID}", json=update_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["name"] == "Updated Door"
                assert data["security_level"] == "high"
            finally:
                self.cleanup_overrides(client)

    def test_set_door_status_success(self, client, mock_admin_user):
        """Test setting door status"""
        with patch('app.api.v1.doors.SetDoorStatusUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock door with updated status
            now = datetime.now(UTC).replace(tzinfo=None)
            door = Door(
                id=SAMPLE_DOOR_UUID,
                name="Test Door",
                location="Building A",
                door_type=DoorType.ENTRANCE,
                security_level=SecurityLevel.MEDIUM,
                status=DoorStatus.MAINTENANCE,
                created_at=now,
                updated_at=now,
                description="Test door",
                default_schedule=None,
                requires_pin=False,
                max_attempts=3,
                lockout_duration=300,
                failed_attempts=0
            )
            mock_use_case.execute.return_value = door
            
            status_data = {"status": "maintenance"}
            
            try:
                response = client.post(f"/api/v1/doors/{SAMPLE_DOOR_UUID}/status", json=status_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "maintenance"
            finally:
                self.cleanup_overrides(client)

    def test_delete_door_success(self, client, mock_admin_user):
        """Test successful door deletion"""
        with patch('app.api.v1.doors.DeleteDoorUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = True
            
            try:
                response = client.delete(f"/api/v1/doors/{SAMPLE_DOOR_UUID}", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 204
            finally:
                self.cleanup_overrides(client)

    def test_delete_door_not_found(self, client, mock_admin_user):
        """Test door deletion when door doesn't exist"""
        with patch('app.api.v1.doors.DeleteDoorUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = False
            
            try:
                response = client.delete(f"/api/v1/doors/{SAMPLE_DOOR_UUID}", headers={"Authorization": "Bearer fake_token"})
                
                # Verify not found response
                assert response.status_code == 404
            finally:
                self.cleanup_overrides(client)