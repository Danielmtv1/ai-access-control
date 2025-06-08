import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime, UTC, timedelta, time
from app.domain.entities.door import Door, DoorType, SecurityLevel, DoorStatus, AccessSchedule

class TestDoorsAPI:
    """Integration tests for Doors API endpoints"""
    
    @pytest.fixture
    def admin_jwt_token(self, auth_service, sample_admin_user):
        """Valid JWT token for admin user"""
        return auth_service.generate_access_token(sample_admin_user)
    
    @pytest.fixture
    def admin_headers(self, admin_jwt_token):
        """Headers with admin JWT token"""
        return {"Authorization": f"Bearer {admin_jwt_token}"}
    
    def test_create_door_success(self, client: TestClient, admin_headers):
        """Test successful door creation"""
        with patch('app.api.v1.doors.CreateDoorUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock successful door creation
            now = datetime.now(UTC).replace(tzinfo=None)
            schedule = AccessSchedule(
                days_of_week=[0, 1, 2, 3, 4],
                start_time=time(9, 0),
                end_time=time(18, 0)
            )
            created_door = Door(
                id=1,
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
            mock_use_case.execute.return_value = created_door
            
            # Make request
            door_data = {
                "name": "Main Entrance",
                "location": "Building A",
                "description": "Main building entrance",
                "door_type": "entrance",
                "security_level": "medium",
                "requires_pin": False,
                "max_attempts": 3,
                "lockout_duration": 300,
                "default_schedule": {
                    "days_of_week": [0, 1, 2, 3, 4],
                    "start_time": "09:00",
                    "end_time": "18:00"
                }
            }
            
            response = client.post("/api/v1/doors/", json=door_data, headers=admin_headers)
            
            # Verify response
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Main Entrance"
            assert data["location"] == "Building A"
            assert data["door_type"] == "entrance"
            assert data["security_level"] == "medium"
            assert data["status"] == "active"
            assert data["default_schedule"] is not None
            assert data["default_schedule"]["days_of_week"] == [0, 1, 2, 3, 4]
    
    def test_create_door_without_schedule(self, client: TestClient, admin_headers):
        """Test door creation without schedule"""
        with patch('app.api.v1.doors.CreateDoorUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock door creation without schedule
            now = datetime.now(UTC).replace(tzinfo=None)
            created_door = Door(
                id=1,
                name="Emergency Exit",
                location="Building A",
                door_type=DoorType.EMERGENCY,
                security_level=SecurityLevel.CRITICAL,
                status=DoorStatus.ACTIVE,
                created_at=now,
                updated_at=now,
                default_schedule=None
            )
            mock_use_case.execute.return_value = created_door
            
            # Make request
            door_data = {
                "name": "Emergency Exit",
                "location": "Building A",
                "door_type": "emergency",
                "security_level": "critical"
            }
            
            response = client.post("/api/v1/doors/", json=door_data, headers=admin_headers)
            
            # Verify response
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Emergency Exit"
            assert data["default_schedule"] is None
    
    def test_create_door_unauthorized(self, client: TestClient):
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
    
    def test_create_door_validation_error(self, client: TestClient, admin_headers):
        """Test door creation with validation errors"""
        # Invalid door data
        door_data = {
            "name": "",  # Empty name
            "location": "",  # Empty location
            "door_type": "invalid_type",  # Invalid door type
            "security_level": "invalid_level",  # Invalid security level
            "max_attempts": -1,  # Invalid max attempts
            "lockout_duration": 30  # Below minimum
        }
        
        response = client.post("/api/v1/doors/", json=door_data, headers=admin_headers)
        
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert len(errors) > 0
    
    def test_get_door_success(self, client: TestClient, admin_headers):
        """Test successful door retrieval"""
        with patch('app.api.v1.doors.GetDoorUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock door retrieval
            now = datetime.now(UTC).replace(tzinfo=None)
            schedule = AccessSchedule(
                days_of_week=[5, 6],  # Weekends
                start_time=time(10, 0),
                end_time=time(16, 0)
            )
            door = Door(
                id=1,
                name="Weekend Door",
                location="Building B",
                door_type=DoorType.BIDIRECTIONAL,
                security_level=SecurityLevel.HIGH,
                status=DoorStatus.ACTIVE,
                created_at=now,
                updated_at=now,
                default_schedule=schedule,
                requires_pin=True,
                failed_attempts=2
            )
            mock_use_case.execute.return_value = door
            
            # Make request
            response = client.get("/api/v1/doors/1", headers=admin_headers)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "Weekend Door"
            assert data["security_level"] == "high"
            assert data["requires_pin"] is True
            assert data["failed_attempts"] == 2
    
    def test_get_door_not_found(self, client: TestClient, admin_headers):
        """Test door retrieval when door doesn't exist"""
        with patch('app.api.v1.doors.GetDoorUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock door not found
            from app.application.use_cases.door_use_cases import DoorNotFoundError
            mock_use_case.execute.side_effect = DoorNotFoundError("Door with ID 999 not found")
            
            # Make request
            response = client.get("/api/v1/doors/999", headers=admin_headers)
            
            # Verify response
            assert response.status_code == 404
    
    def test_get_door_by_name_success(self, client: TestClient, admin_headers):
        """Test successful door retrieval by name"""
        with patch('app.api.v1.doors.GetDoorByNameUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock door retrieval
            now = datetime.now(UTC).replace(tzinfo=None)
            door = Door(
                id=1,
                name="Server Room",
                location="Building A",
                door_type=DoorType.ENTRANCE,
                security_level=SecurityLevel.CRITICAL,
                status=DoorStatus.ACTIVE,
                created_at=now,
                updated_at=now,
                requires_pin=True
            )
            mock_use_case.execute.return_value = door
            
            # Make request
            response = client.get("/api/v1/doors/by-name/Server Room", headers=admin_headers)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Server Room"
            assert data["security_level"] == "critical"
    
    def test_get_doors_by_location_success(self, client: TestClient, admin_headers):
        """Test successful doors retrieval by location"""
        with patch('app.api.v1.doors.GetDoorsByLocationUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock multiple doors in same location
            now = datetime.now(UTC).replace(tzinfo=None)
            doors = [
                Door(
                    id=1,
                    name="Front Door",
                    location="Building A",
                    door_type=DoorType.ENTRANCE,
                    security_level=SecurityLevel.MEDIUM,
                    status=DoorStatus.ACTIVE,
                    created_at=now,
                    updated_at=now
                ),
                Door(
                    id=2,
                    name="Back Door",
                    location="Building A",
                    door_type=DoorType.EXIT,
                    security_level=SecurityLevel.LOW,
                    status=DoorStatus.ACTIVE,
                    created_at=now,
                    updated_at=now
                )
            ]
            mock_use_case.execute.return_value = doors
            
            # Make request
            response = client.get("/api/v1/doors/location/Building A", headers=admin_headers)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert all(door["location"] == "Building A" for door in data)
    
    def test_get_doors_by_security_level_success(self, client: TestClient, admin_headers):
        """Test successful doors retrieval by security level"""
        with patch('app.api.v1.doors.GetDoorsBySecurityLevelUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock high security doors
            now = datetime.now(UTC).replace(tzinfo=None)
            doors = [
                Door(
                    id=1,
                    name="Vault Door",
                    location="Building A",
                    door_type=DoorType.ENTRANCE,
                    security_level=SecurityLevel.HIGH,
                    status=DoorStatus.ACTIVE,
                    created_at=now,
                    updated_at=now,
                    requires_pin=True
                )
            ]
            mock_use_case.execute.return_value = doors
            
            # Make request
            response = client.get("/api/v1/doors/security-level/high", headers=admin_headers)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["security_level"] == "high"
            assert data[0]["requires_pin"] is True
    
    def test_list_doors_success(self, client: TestClient, admin_headers):
        """Test successful doors listing with pagination"""
        with patch('app.api.v1.doors.ListDoorsUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock paginated doors
            now = datetime.now(UTC).replace(tzinfo=None)
            doors = [
                Door(
                    id=i,
                    name=f"Door {i}",
                    location="Building A",
                    door_type=DoorType.ENTRANCE,
                    security_level=SecurityLevel.MEDIUM,
                    status=DoorStatus.ACTIVE,
                    created_at=now,
                    updated_at=now
                )
                for i in range(1, 4)
            ]
            mock_use_case.execute.return_value = doors
            
            # Make request with pagination
            response = client.get("/api/v1/doors/?skip=0&limit=3", headers=admin_headers)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert "doors" in data
            assert "total" in data
            assert "skip" in data
            assert "limit" in data
            assert len(data["doors"]) == 3
    
    def test_list_doors_active_only(self, client: TestClient, admin_headers):
        """Test listing only active doors"""
        with patch('app.api.v1.doors.GetActiveDoorsUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock only active doors
            now = datetime.now(UTC).replace(tzinfo=None)
            doors = [
                Door(
                    id=1,
                    name="Active Door",
                    location="Building A",
                    door_type=DoorType.ENTRANCE,
                    security_level=SecurityLevel.MEDIUM,
                    status=DoorStatus.ACTIVE,
                    created_at=now,
                    updated_at=now
                )
            ]
            mock_use_case.execute.return_value = doors
            
            # Make request for active only
            response = client.get("/api/v1/doors/?active_only=true", headers=admin_headers)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert all(door["status"] == "active" for door in data["doors"])
    
    def test_update_door_success(self, client: TestClient, admin_headers):
        """Test successful door update"""
        with patch('app.api.v1.doors.UpdateDoorUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock updated door
            now = datetime.now(UTC).replace(tzinfo=None)
            new_schedule = AccessSchedule(
                days_of_week=[0, 1, 2, 3, 4, 5, 6],  # All week
                start_time=time(8, 0),
                end_time=time(20, 0)
            )
            updated_door = Door(
                id=1,
                name="Updated Door Name",
                location="Building A",
                door_type=DoorType.ENTRANCE,
                security_level=SecurityLevel.HIGH,  # Updated
                status=DoorStatus.ACTIVE,
                created_at=now,
                updated_at=now + timedelta(minutes=1),
                default_schedule=new_schedule,  # Updated
                requires_pin=True  # Updated
            )
            mock_use_case.execute.return_value = updated_door
            
            # Make request
            update_data = {
                "name": "Updated Door Name",
                "security_level": "high",
                "requires_pin": True,
                "default_schedule": {
                    "days_of_week": [0, 1, 2, 3, 4, 5, 6],
                    "start_time": "08:00",
                    "end_time": "20:00"
                }
            }
            response = client.put("/api/v1/doors/1", json=update_data, headers=admin_headers)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Door Name"
            assert data["security_level"] == "high"
            assert data["requires_pin"] is True
    
    def test_set_door_status_success(self, client: TestClient, admin_headers):
        """Test successful door status change"""
        with patch('app.api.v1.doors.SetDoorStatusUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock door with updated status
            now = datetime.now(UTC).replace(tzinfo=None)
            maintenance_door = Door(
                id=1,
                name="Main Door",
                location="Building A",
                door_type=DoorType.ENTRANCE,
                security_level=SecurityLevel.MEDIUM,
                status=DoorStatus.MAINTENANCE,  # Updated
                created_at=now,
                updated_at=now + timedelta(minutes=1)
            )
            mock_use_case.execute.return_value = maintenance_door
            
            # Make request
            status_data = {"status": "maintenance"}
            response = client.post("/api/v1/doors/1/status", json=status_data, headers=admin_headers)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "maintenance"
    
    def test_delete_door_success(self, client: TestClient, admin_headers):
        """Test successful door deletion"""
        with patch('app.api.v1.doors.DeleteDoorUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock successful deletion
            mock_use_case.execute.return_value = True
            
            # Make request
            response = client.delete("/api/v1/doors/1", headers=admin_headers)
            
            # Verify response
            assert response.status_code == 204
    
    def test_delete_door_not_found(self, client: TestClient, admin_headers):
        """Test door deletion when door doesn't exist"""
        with patch('app.api.v1.doors.DeleteDoorUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock door not found
            from app.application.use_cases.door_use_cases import DoorNotFoundError
            mock_use_case.execute.side_effect = DoorNotFoundError("Door with ID 999 not found")
            
            # Make request
            response = client.delete("/api/v1/doors/999", headers=admin_headers)
            
            # Verify response
            assert response.status_code == 404