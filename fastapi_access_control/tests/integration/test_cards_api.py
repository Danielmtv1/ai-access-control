import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, UTC, timedelta
from app.domain.entities.card import Card, CardType, CardStatus
from app.domain.entities.user import User, Role, UserStatus

class TestCardsAPI:
    """Integration tests for Cards API endpoints"""
    
    @pytest.fixture
    def authenticated_headers(self, valid_jwt_token):
        """Headers with valid JWT token"""
        return {"Authorization": f"Bearer {valid_jwt_token}"}
    
    @pytest.fixture
    def admin_jwt_token(self, auth_service, sample_admin_user):
        """Valid JWT token for admin user"""
        return auth_service.generate_access_token(sample_admin_user)
    
    @pytest.fixture
    def admin_headers(self, admin_jwt_token):
        """Headers with admin JWT token"""
        return {"Authorization": f"Bearer {admin_jwt_token}"}
    
    def test_create_card_success(self, client: TestClient, admin_headers):
        """Test successful card creation"""
        with patch('app.api.v1.cards.CreateCardUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock successful card creation
            now = datetime.now(UTC).replace(tzinfo=None)
            created_card = Card(
                id=1,
                card_id="CARD001",
                user_id=1,
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
                "user_id": 1,
                "card_type": "employee",
                "valid_from": "2024-01-01T00:00:00",
                "valid_until": "2024-12-31T23:59:59"
            }
            
            response = client.post("/api/v1/cards/", json=card_data, headers=admin_headers)
            
            # Verify response
            assert response.status_code == 201
            data = response.json()
            assert data["card_id"] == "CARD001"
            assert data["user_id"] == 1
            assert data["card_type"] == "employee"
            assert data["status"] == "active"
    
    def test_create_card_unauthorized(self, client: TestClient):
        """Test card creation without authentication"""
        card_data = {
            "card_id": "CARD001",
            "user_id": 1,
            "card_type": "employee",
            "valid_from": "2024-01-01T00:00:00"
        }
        
        response = client.post("/api/v1/cards/", json=card_data)
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_create_card_validation_error(self, client: TestClient, admin_headers):
        """Test card creation with validation errors"""
        # Invalid card data (missing required fields)
        card_data = {
            "card_id": "",  # Empty card_id
            "user_id": 0,   # Invalid user_id
            "card_type": "invalid_type",  # Invalid card type
            "valid_from": "invalid_date"  # Invalid date format
        }
        
        response = client.post("/api/v1/cards/", json=card_data, headers=admin_headers)
        
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("card_id" in str(error) for error in errors)
        assert any("user_id" in str(error) for error in errors)
    
    def test_get_card_success(self, client: TestClient, admin_headers):
        """Test successful card retrieval"""
        with patch('app.api.v1.cards.GetCardUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock card retrieval
            now = datetime.now(UTC).replace(tzinfo=None)
            card = Card(
                id=1,
                card_id="CARD001",
                user_id=1,
                card_type=CardType.EMPLOYEE,
                status=CardStatus.ACTIVE,
                valid_from=now,
                valid_until=now + timedelta(days=365),
                created_at=now,
                updated_at=now,
                use_count=5
            )
            mock_use_case.execute.return_value = card
            
            # Make request
            response = client.get("/api/v1/cards/1", headers=admin_headers)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["card_id"] == "CARD001"
            assert data["use_count"] == 5
    
    def test_get_card_not_found(self, client: TestClient, admin_headers):
        """Test card retrieval when card doesn't exist"""
        with patch('app.api.v1.cards.GetCardUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock card not found
            from app.application.use_cases.card_use_cases import CardNotFoundError
            mock_use_case.execute.side_effect = CardNotFoundError("Card with ID 999 not found")
            
            # Make request
            response = client.get("/api/v1/cards/999", headers=admin_headers)
            
            # Verify response
            assert response.status_code == 404
    
    def test_get_card_by_card_id_success(self, client: TestClient, admin_headers):
        """Test successful card retrieval by card_id"""
        with patch('app.api.v1.cards.GetCardByCardIdUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock card retrieval
            now = datetime.now(UTC).replace(tzinfo=None)
            card = Card(
                id=1,
                card_id="CARD001",
                user_id=1,
                card_type=CardType.VISITOR,
                status=CardStatus.ACTIVE,
                valid_from=now,
                valid_until=now + timedelta(days=1),
                created_at=now,
                updated_at=now,
                use_count=0
            )
            mock_use_case.execute.return_value = card
            
            # Make request
            response = client.get("/api/v1/cards/by-card-id/CARD001", headers=admin_headers)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["card_id"] == "CARD001"
            assert data["card_type"] == "visitor"
    
    def test_get_user_cards_success(self, client: TestClient, admin_headers):
        """Test successful user cards retrieval"""
        with patch('app.api.v1.cards.GetUserCardsUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock multiple cards for user
            now = datetime.now(UTC).replace(tzinfo=None)
            cards = [
                Card(
                    id=1,
                    card_id="CARD001",
                    user_id=1,
                    card_type=CardType.EMPLOYEE,
                    status=CardStatus.ACTIVE,
                    valid_from=now,
                    valid_until=None,
                    created_at=now,
                    updated_at=now,
                    use_count=0
                ),
                Card(
                    id=2,
                    card_id="CARD002",
                    user_id=1,
                    card_type=CardType.TEMPORARY,
                    status=CardStatus.ACTIVE,
                    valid_from=now,
                    valid_until=now + timedelta(days=1),
                    created_at=now,
                    updated_at=now,
                    use_count=0
                )
            ]
            mock_use_case.execute.return_value = cards
            
            # Make request
            response = client.get("/api/v1/cards/user/1", headers=admin_headers)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["card_id"] == "CARD001"
            assert data[1]["card_id"] == "CARD002"
    
    def test_list_cards_success(self, client: TestClient, admin_headers):
        """Test successful cards listing with pagination"""
        with patch('app.api.v1.cards.ListCardsUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock paginated cards
            now = datetime.now(UTC).replace(tzinfo=None)
            cards = [
                Card(
                    id=i,
                    card_id=f"CARD{i:03d}",
                    user_id=1,
                    card_type=CardType.EMPLOYEE,
                    status=CardStatus.ACTIVE,
                    valid_from=now,
                    valid_until=None,
                    created_at=now,
                    updated_at=now,
                    use_count=0
                )
                for i in range(1, 6)
            ]
            mock_use_case.execute.return_value = cards
            
            # Make request with pagination
            response = client.get("/api/v1/cards/?skip=0&limit=5", headers=admin_headers)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert "cards" in data
            assert "total" in data
            assert "skip" in data
            assert "limit" in data
            assert len(data["cards"]) == 5
            assert data["skip"] == 0
            assert data["limit"] == 5
    
    def test_update_card_success(self, client: TestClient, admin_headers):
        """Test successful card update"""
        with patch('app.api.v1.cards.UpdateCardUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock updated card
            now = datetime.now(UTC).replace(tzinfo=None)
            updated_card = Card(
                id=1,
                card_id="CARD001",
                user_id=1,
                card_type=CardType.VISITOR,  # Updated
                status=CardStatus.SUSPENDED,  # Updated
                valid_from=now,
                valid_until=now + timedelta(days=30),  # Updated
                created_at=now,
                updated_at=now + timedelta(minutes=1),
                use_count=0
            )
            mock_use_case.execute.return_value = updated_card
            
            # Make request
            update_data = {
                "card_type": "visitor",
                "status": "suspended",
                "valid_until": "2024-07-01T23:59:59"
            }
            response = client.put("/api/v1/cards/1", json=update_data, headers=admin_headers)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["card_type"] == "visitor"
            assert data["status"] == "suspended"
    
    def test_suspend_card_success(self, client: TestClient, admin_headers):
        """Test successful card suspension"""
        with patch('app.api.v1.cards.SuspendCardUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock suspended card
            now = datetime.now(UTC).replace(tzinfo=None)
            suspended_card = Card(
                id=1,
                card_id="CARD001",
                user_id=1,
                card_type=CardType.EMPLOYEE,
                status=CardStatus.SUSPENDED,  # Updated by domain logic
                valid_from=now,
                valid_until=None,
                created_at=now,
                updated_at=now + timedelta(minutes=1),
                use_count=0
            )
            mock_use_case.execute.return_value = suspended_card
            
            # Make request
            response = client.post("/api/v1/cards/1/suspend", headers=admin_headers)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "suspended"
    
    def test_deactivate_card_success(self, client: TestClient, admin_headers):
        """Test successful card deactivation"""
        with patch('app.api.v1.cards.DeactivateCardUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock deactivated card
            now = datetime.now(UTC).replace(tzinfo=None)
            deactivated_card = Card(
                id=1,
                card_id="CARD001",
                user_id=1,
                card_type=CardType.EMPLOYEE,
                status=CardStatus.INACTIVE,  # Updated by domain logic
                valid_from=now,
                valid_until=None,
                created_at=now,
                updated_at=now + timedelta(minutes=1),
                use_count=0
            )
            mock_use_case.execute.return_value = deactivated_card
            
            # Make request
            response = client.post("/api/v1/cards/1/deactivate", headers=admin_headers)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "inactive"
    
    def test_delete_card_success(self, client: TestClient, admin_headers):
        """Test successful card deletion"""
        with patch('app.api.v1.cards.DeleteCardUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock successful deletion
            mock_use_case.execute.return_value = True
            
            # Make request
            response = client.delete("/api/v1/cards/1", headers=admin_headers)
            
            # Verify response
            assert response.status_code == 204
    
    def test_delete_card_not_found(self, client: TestClient, admin_headers):
        """Test card deletion when card doesn't exist"""
        with patch('app.api.v1.cards.DeleteCardUseCase') as mock_use_case_class:
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock card not found
            from app.application.use_cases.card_use_cases import CardNotFoundError
            mock_use_case.execute.side_effect = CardNotFoundError("Card with ID 999 not found")
            
            # Make request
            response = client.delete("/api/v1/cards/999", headers=admin_headers)
            
            # Verify response
            assert response.status_code == 404