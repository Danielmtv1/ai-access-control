import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, UTC, timedelta
from app.domain.entities.card import Card, CardType, CardStatus
from app.domain.entities.user import User, Role, UserStatus
from tests.conftest import SAMPLE_USER_UUID, SAMPLE_CARD_UUID, SAMPLE_CARD_UUID_2, SAMPLE_ADMIN_UUID

class TestCardsAPI:
    """Integration tests for Cards API endpoints"""
    
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

    def test_create_card_success(self, client, mock_admin_user):
        """Test successful card creation"""
        with patch('app.api.v1.cards.CreateCardUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock successful card creation
            now = datetime.now(UTC).replace(tzinfo=None)
            created_card = Card(
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
            mock_use_case.execute.return_value = created_card
            
            # Make request
            card_data = {
                "card_id": "CARD001",
                "user_id": str(SAMPLE_USER_UUID),
                "card_type": "employee",
                "valid_from": now.isoformat(),
                "valid_until": (now + timedelta(days=365)).isoformat()
            }
            
            try:
                response = client.post("/api/v1/cards/", json=card_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 201
                data = response.json()
                assert data["card_id"] == "CARD001"
                assert data["card_type"] == "employee"
                assert data["status"] == "active"
            finally:
                self.cleanup_overrides(client)

    def test_create_card_unauthorized(self, client):
        """Test card creation without authentication"""
        card_data = {
            "card_id": "CARD001",
            "user_id": str(SAMPLE_USER_UUID),
            "card_type": "employee"
        }
        
        response = client.post("/api/v1/cards/", json=card_data)
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_create_card_validation_error(self, client, mock_admin_user):
        """Test card creation with invalid data"""
        # Setup authentication
        self.setup_auth_override(client, mock_admin_user)
        
        try:
            # Make request with invalid data
            card_data = {
                "card_id": "",  # Empty card_id should fail validation
                "user_id": "invalid-uuid",  # Invalid UUID
                "card_type": "invalid_type"  # Invalid card type
            }
            
            response = client.post("/api/v1/cards/", json=card_data, headers={"Authorization": "Bearer fake_token"})
            
            # Verify validation error
            assert response.status_code == 422
        finally:
            self.cleanup_overrides(client)

    def test_get_card_success(self, client, mock_admin_user):
        """Test successful card retrieval"""
        with patch('app.api.v1.cards.GetCardUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock card retrieval
            now = datetime.now(UTC).replace(tzinfo=None)
            card = Card(
                id=SAMPLE_CARD_UUID,
                card_id="CARD001",
                user_id=SAMPLE_USER_UUID,
                card_type=CardType.EMPLOYEE,
                status=CardStatus.ACTIVE,
                valid_from=now,
                valid_until=now + timedelta(days=365),
                created_at=now,
                updated_at=now,
                use_count=5
            )
            mock_use_case.execute.return_value = card
            
            try:
                response = client.get(f"/api/v1/cards/{SAMPLE_CARD_UUID}", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["card_id"] == "CARD001"
                assert data["id"] == str(SAMPLE_CARD_UUID)
                assert data["use_count"] == 5
            finally:
                self.cleanup_overrides(client)

    def test_get_card_not_found(self, client, mock_admin_user):
        """Test card retrieval when card doesn't exist"""
        with patch('app.api.v1.cards.GetCardUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            from app.domain.exceptions import EntityNotFoundError
            mock_use_case.execute.side_effect = EntityNotFoundError("Card not found")
            
            try:
                response = client.get(f"/api/v1/cards/{SAMPLE_CARD_UUID}", headers={"Authorization": "Bearer fake_token"})
                
                # Verify not found response
                assert response.status_code == 404
            finally:
                self.cleanup_overrides(client)

    def test_get_card_by_card_id_success(self, client, mock_admin_user):
        """Test card retrieval by card_id"""
        with patch('app.api.v1.cards.GetCardByCardIdUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock card retrieval
            now = datetime.now(UTC).replace(tzinfo=None)
            card = Card(
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
            mock_use_case.execute.return_value = card
            
            try:
                response = client.get("/api/v1/cards/by-card-id/CARD001", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["card_id"] == "CARD001"
            finally:
                self.cleanup_overrides(client)

    def test_get_user_cards_success(self, client, mock_admin_user):
        """Test retrieving cards for a user"""
        with patch('app.api.v1.cards.GetUserCardsUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock cards retrieval
            now = datetime.now(UTC).replace(tzinfo=None)
            cards = [
                Card(
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
                ),
                Card(
                    id=SAMPLE_CARD_UUID_2,
                    card_id="CARD002",
                    user_id=SAMPLE_USER_UUID,
                    card_type=CardType.VISITOR,
                    status=CardStatus.ACTIVE,
                    valid_from=now,
                    valid_until=now + timedelta(days=30),
                    created_at=now,
                    updated_at=now,
                    use_count=0
                )
            ]
            mock_use_case.execute.return_value = cards
            
            try:
                response = client.get(f"/api/v1/cards/user/{SAMPLE_USER_UUID}", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2
                assert data[0]["user_id"] == str(SAMPLE_USER_UUID)
            finally:
                self.cleanup_overrides(client)

    def test_list_cards_success(self, client, mock_admin_user):
        """Test listing all cards"""
        with patch('app.api.v1.cards.ListCardsUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock cards retrieval
            now = datetime.now(UTC).replace(tzinfo=None)
            cards = [
                Card(
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
            ]
            mock_use_case.execute.return_value = cards
            
            try:
                response = client.get("/api/v1/cards/", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert len(data["cards"]) == 1
            finally:
                self.cleanup_overrides(client)

    def test_update_card_success(self, client, mock_admin_user):
        """Test successful card update"""
        with patch('app.api.v1.cards.UpdateCardUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock updated card
            now = datetime.now(UTC).replace(tzinfo=None)
            updated_card = Card(
                id=SAMPLE_CARD_UUID,
                card_id="CARD001",
                user_id=SAMPLE_USER_UUID,
                card_type=CardType.CONTRACTOR,
                status=CardStatus.ACTIVE,
                valid_from=now,
                valid_until=now + timedelta(days=180),
                created_at=now,
                updated_at=now,
                use_count=0
            )
            mock_use_case.execute.return_value = updated_card
            
            update_data = {
                "card_type": "contractor",
                "valid_until": (now + timedelta(days=180)).isoformat()
            }
            
            try:
                response = client.put(f"/api/v1/cards/{SAMPLE_CARD_UUID}", json=update_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["card_type"] == "contractor"
            finally:
                self.cleanup_overrides(client)

    def test_suspend_card_success(self, client, mock_admin_user):
        """Test card suspension"""
        with patch('app.api.v1.cards.SuspendCardUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock suspended card
            now = datetime.now(UTC).replace(tzinfo=None)
            card = Card(
                id=SAMPLE_CARD_UUID,
                card_id="CARD001",
                user_id=SAMPLE_USER_UUID,
                card_type=CardType.EMPLOYEE,
                status=CardStatus.SUSPENDED,
                valid_from=now,
                valid_until=now + timedelta(days=365),
                created_at=now,
                updated_at=now,
                use_count=0
            )
            mock_use_case.execute.return_value = card
            
            try:
                response = client.post(f"/api/v1/cards/{SAMPLE_CARD_UUID}/suspend", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "suspended"
            finally:
                self.cleanup_overrides(client)

    def test_deactivate_card_success(self, client, mock_admin_user):
        """Test card deactivation"""
        with patch('app.api.v1.cards.DeactivateCardUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock deactivated card
            now = datetime.now(UTC).replace(tzinfo=None)
            card = Card(
                id=SAMPLE_CARD_UUID,
                card_id="CARD001",
                user_id=SAMPLE_USER_UUID,
                card_type=CardType.EMPLOYEE,
                status=CardStatus.INACTIVE,
                valid_from=now,
                valid_until=now + timedelta(days=365),
                created_at=now,
                updated_at=now,
                use_count=0
            )
            mock_use_case.execute.return_value = card
            
            try:
                response = client.post(f"/api/v1/cards/{SAMPLE_CARD_UUID}/deactivate", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "inactive"
            finally:
                self.cleanup_overrides(client)

    def test_delete_card_success(self, client, mock_admin_user):
        """Test successful card deletion"""
        with patch('app.api.v1.cards.DeleteCardUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = True
            
            try:
                response = client.delete(f"/api/v1/cards/{SAMPLE_CARD_UUID}", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 204
            finally:
                self.cleanup_overrides(client)

    def test_delete_card_not_found(self, client, mock_admin_user):
        """Test card deletion when card doesn't exist"""
        with patch('app.api.v1.cards.DeleteCardUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = False
            
            try:
                response = client.delete(f"/api/v1/cards/{SAMPLE_CARD_UUID}", headers={"Authorization": "Bearer fake_token"})
                
                # Verify not found response
                assert response.status_code == 404
            finally:
                self.cleanup_overrides(client)