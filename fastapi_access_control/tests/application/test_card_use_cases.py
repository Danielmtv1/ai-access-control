import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timezone, UTC, timedelta
from app.application.use_cases.card_use_cases import (
    CreateCardUseCase, GetCardUseCase, GetCardByCardIdUseCase, GetUserCardsUseCase,
    UpdateCardUseCase, DeactivateCardUseCase, SuspendCardUseCase, ListCardsUseCase, 
    DeleteCardUseCase, CardNotFoundError
)
from app.domain.entities.card import Card, CardType, CardStatus
from app.domain.entities.user import User, Role, UserStatus
from app.domain.exceptions import DomainError

class TestCreateCardUseCase:
    """Test cases for CreateCardUseCase"""
    
    @pytest.fixture
    def mock_card_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_user_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def sample_user(self):
        now = datetime.now(UTC).replace(tzinfo=None)
        return User(
            id=1,
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
    
    @pytest.fixture
    def create_card_use_case(self, mock_card_repository, mock_user_repository):
        return CreateCardUseCase(mock_card_repository, mock_user_repository)
    
    @pytest.mark.asyncio
    async def test_create_card_success(self, create_card_use_case, mock_card_repository, mock_user_repository, sample_user):
        """Test successful card creation"""
        now = datetime.now(UTC).replace(tzinfo=None)
        valid_until = now + timedelta(days=365)
        
        # Mock user exists
        mock_user_repository.get_by_id.return_value = sample_user
        
        # Mock card doesn't exist
        mock_card_repository.get_by_card_id.return_value = None
        
        # Mock card creation
        expected_card = Card(
            id=1,
            card_id="CARD001",
            user_id=1,
            card_type=CardType.EMPLOYEE,
            status=CardStatus.ACTIVE,
            valid_from=now,
            valid_until=valid_until,
            created_at=now,
            updated_at=now,
            use_count=0
        )
        mock_card_repository.create.return_value = expected_card
        
        # Execute use case
        result = await create_card_use_case.execute(
            card_id="CARD001",
            user_id=1,
            card_type="employee",
            valid_from=now,
            valid_until=valid_until
        )
        
        # Verify
        assert result.card_id == "CARD001"
        assert result.user_id == 1
        assert result.card_type == CardType.EMPLOYEE
        mock_user_repository.get_by_id.assert_called_once_with(1)
        mock_card_repository.get_by_card_id.assert_called_once_with("CARD001")
        mock_card_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_card_user_not_found(self, create_card_use_case, mock_card_repository, mock_user_repository):
        """Test card creation fails when user doesn't exist"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        # Mock user doesn't exist
        mock_user_repository.get_by_id.return_value = None
        
        # Execute and verify exception
        with pytest.raises(DomainError, match="User with ID 999 not found"):
            await create_card_use_case.execute(
                card_id="CARD001",
                user_id=999,
                card_type="employee",
                valid_from=now
            )
        
        mock_user_repository.get_by_id.assert_called_once_with(999)
        mock_card_repository.get_by_card_id.assert_not_called()
        mock_card_repository.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_card_duplicate_card_id(self, create_card_use_case, mock_card_repository, mock_user_repository, sample_user):
        """Test card creation fails when card_id already exists"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        # Mock user exists
        mock_user_repository.get_by_id.return_value = sample_user
        
        # Mock card already exists
        existing_card = Card(
            id=2,
            card_id="CARD001",
            user_id=2,
            card_type=CardType.EMPLOYEE,
            status=CardStatus.ACTIVE,
            valid_from=now,
            valid_until=None,
            created_at=now,
            updated_at=now,
            use_count=0
        )
        mock_card_repository.get_by_card_id.return_value = existing_card
        
        # Execute and verify exception
        with pytest.raises(DomainError, match="Card with ID CARD001 already exists"):
            await create_card_use_case.execute(
                card_id="CARD001",
                user_id=1,
                card_type="employee",
                valid_from=now
            )
        
        mock_user_repository.get_by_id.assert_called_once_with(1)
        mock_card_repository.get_by_card_id.assert_called_once_with("CARD001")
        mock_card_repository.create.assert_not_called()

class TestGetCardUseCase:
    """Test cases for GetCardUseCase"""
    
    @pytest.fixture
    def mock_card_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def get_card_use_case(self, mock_card_repository):
        return GetCardUseCase(mock_card_repository)
    
    @pytest.mark.asyncio
    async def test_get_card_success(self, get_card_use_case, mock_card_repository):
        """Test successful card retrieval"""
        now = datetime.now(UTC).replace(tzinfo=None)
        expected_card = Card(
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
        )
        mock_card_repository.get_by_id.return_value = expected_card
        
        result = await get_card_use_case.execute(1)
        
        assert result == expected_card
        mock_card_repository.get_by_id.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_card_not_found(self, get_card_use_case, mock_card_repository):
        """Test card retrieval when card doesn't exist"""
        mock_card_repository.get_by_id.return_value = None
        
        with pytest.raises(CardNotFoundError, match="Card with ID 999 not found"):
            await get_card_use_case.execute(999)
        
        mock_card_repository.get_by_id.assert_called_once_with(999)

class TestUpdateCardUseCase:
    """Test cases for UpdateCardUseCase"""
    
    @pytest.fixture
    def mock_card_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def update_card_use_case(self, mock_card_repository):
        return UpdateCardUseCase(mock_card_repository)
    
    @pytest.mark.asyncio
    async def test_update_card_success(self, update_card_use_case, mock_card_repository):
        """Test successful card update"""
        now = datetime.now(UTC).replace(tzinfo=None)
        original_card = Card(
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
        )
        
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
        
        mock_card_repository.get_by_id.return_value = original_card
        mock_card_repository.update.return_value = updated_card
        
        result = await update_card_use_case.execute(
            card_id=1,
            card_type="visitor",
            status="suspended",
            valid_until=now + timedelta(days=30)
        )
        
        assert result.card_type == CardType.VISITOR
        assert result.status == CardStatus.SUSPENDED
        assert result.valid_until == now + timedelta(days=30)
        mock_card_repository.get_by_id.assert_called_once_with(1)
        mock_card_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_card_not_found(self, update_card_use_case, mock_card_repository):
        """Test card update when card doesn't exist"""
        mock_card_repository.get_by_id.return_value = None
        
        with pytest.raises(CardNotFoundError, match="Card with ID 999 not found"):
            await update_card_use_case.execute(card_id=999, card_type="visitor")
        
        mock_card_repository.get_by_id.assert_called_once_with(999)
        mock_card_repository.update.assert_not_called()

class TestSuspendCardUseCase:
    """Test cases for SuspendCardUseCase"""
    
    @pytest.fixture
    def mock_card_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def suspend_card_use_case(self, mock_card_repository):
        return SuspendCardUseCase(mock_card_repository)
    
    @pytest.mark.asyncio
    async def test_suspend_card_success(self, suspend_card_use_case, mock_card_repository):
        """Test successful card suspension"""
        now = datetime.now(UTC).replace(tzinfo=None)
        original_card = Card(
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
        )
        
        # Simulate card being suspended
        suspended_card = Card(
            id=1,
            card_id="CARD001",
            user_id=1,
            card_type=CardType.EMPLOYEE,
            status=CardStatus.SUSPENDED,  # Updated by domain logic
            valid_from=now,
            valid_until=None,
            created_at=now,
            updated_at=now + timedelta(minutes=1),  # Updated by domain logic
            use_count=0
        )
        
        mock_card_repository.get_by_id.return_value = original_card
        mock_card_repository.update.return_value = suspended_card
        
        result = await suspend_card_use_case.execute(1)
        
        assert result.status == CardStatus.SUSPENDED
        mock_card_repository.get_by_id.assert_called_once_with(1)
        mock_card_repository.update.assert_called_once()

class TestListCardsUseCase:
    """Test cases for ListCardsUseCase"""
    
    @pytest.fixture
    def mock_card_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def list_cards_use_case(self, mock_card_repository):
        return ListCardsUseCase(mock_card_repository)
    
    @pytest.mark.asyncio
    async def test_list_cards_success(self, list_cards_use_case, mock_card_repository):
        """Test successful card listing"""
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
                user_id=2,
                card_type=CardType.VISITOR,
                status=CardStatus.ACTIVE,
                valid_from=now,
                valid_until=now + timedelta(days=1),
                created_at=now,
                updated_at=now,
                use_count=0
            )
        ]
        
        mock_card_repository.list_cards.return_value = cards
        
        result = await list_cards_use_case.execute(skip=0, limit=10)
        
        assert len(result) == 2
        assert result[0].card_id == "CARD001"
        assert result[1].card_id == "CARD002"
        mock_card_repository.list_cards.assert_called_once_with(0, 10)

class TestDeleteCardUseCase:
    """Test cases for DeleteCardUseCase"""
    
    @pytest.fixture
    def mock_card_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def delete_card_use_case(self, mock_card_repository):
        return DeleteCardUseCase(mock_card_repository)
    
    @pytest.mark.asyncio
    async def test_delete_card_success(self, delete_card_use_case, mock_card_repository):
        """Test successful card deletion"""
        now = datetime.now(UTC).replace(tzinfo=None)
        existing_card = Card(
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
        )
        
        mock_card_repository.get_by_id.return_value = existing_card
        mock_card_repository.delete.return_value = True
        
        result = await delete_card_use_case.execute(1)
        
        assert result is True
        mock_card_repository.get_by_id.assert_called_once_with(1)
        mock_card_repository.delete.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_delete_card_not_found(self, delete_card_use_case, mock_card_repository):
        """Test card deletion when card doesn't exist"""
        mock_card_repository.get_by_id.return_value = None
        
        with pytest.raises(CardNotFoundError, match="Card with ID 999 not found"):
            await delete_card_use_case.execute(999)
        
        mock_card_repository.get_by_id.assert_called_once_with(999)
        mock_card_repository.delete.assert_not_called()