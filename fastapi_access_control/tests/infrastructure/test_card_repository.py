import pytest
from datetime import datetime, UTC, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.persistence.adapters.card_repository import SqlAlchemyCardRepository
from app.infrastructure.database.models.card import CardModel
from app.infrastructure.database.models.user import UserModel
from app.domain.entities.card import Card, CardType, CardStatus
from app.domain.exceptions import RepositoryError

class TestSqlAlchemyCardRepository:
    """Test cases for SqlAlchemyCardRepository"""
    
    @pytest.fixture
    async def sample_user_model(self, db_session: AsyncSession):
        """Create a sample user for testing"""
        user_model = UserModel(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            roles=["user"],
            is_active=True
        )
        db_session.add(user_model)
        await db_session.commit()
        await db_session.refresh(user_model)
        return user_model
    
    @pytest.fixture
    async def sample_card_model(self, db_session: AsyncSession, sample_user_model: UserModel):
        """Create a sample card for testing"""
        now = datetime.now(UTC).replace(tzinfo=None)
        card_model = CardModel(
            card_id="CARD001",
            user_id=sample_user_model.id,
            card_type="employee",
            status="active",
            valid_from=now,
            valid_until=now + timedelta(days=365),
            use_count=0
        )
        db_session.add(card_model)
        await db_session.commit()
        await db_session.refresh(card_model)
        return card_model
    
    @pytest.fixture
    def card_repository(self, db_session: AsyncSession):
        """Create card repository for testing"""
        def session_factory():
            return db_session
        return SqlAlchemyCardRepository(session_factory)
    
    async def test_create_card(self, card_repository: SqlAlchemyCardRepository, sample_user_model: UserModel):
        """Test card creation"""
        now = datetime.now(UTC).replace(tzinfo=None)
        valid_until = now + timedelta(days=365)
        
        card = Card(
            id=0,  # Will be set by database
            card_id="CARD002",
            user_id=sample_user_model.id,
            card_type=CardType.EMPLOYEE,
            status=CardStatus.ACTIVE,
            valid_from=now,
            valid_until=valid_until,
            created_at=now,
            updated_at=now,
            use_count=0
        )
        
        result = await card_repository.create(card)
        
        assert result.id > 0
        assert result.card_id == "CARD002"
        assert result.user_id == sample_user_model.id
        assert result.card_type == CardType.EMPLOYEE
        assert result.status == CardStatus.ACTIVE
    
    async def test_get_by_id(self, card_repository: SqlAlchemyCardRepository, sample_card_model: CardModel):
        """Test getting card by ID"""
        result = await card_repository.get_by_id(sample_card_model.id)
        
        assert result is not None
        assert result.id == sample_card_model.id
        assert result.card_id == "CARD001"
        assert result.card_type == CardType.EMPLOYEE
    
    async def test_get_by_id_not_found(self, card_repository: SqlAlchemyCardRepository):
        """Test getting card by ID when card doesn't exist"""
        result = await card_repository.get_by_id(999)
        
        assert result is None
    
    async def test_get_by_card_id(self, card_repository: SqlAlchemyCardRepository, sample_card_model: CardModel):
        """Test getting card by card_id"""
        result = await card_repository.get_by_card_id("CARD001")
        
        assert result is not None
        assert result.id == sample_card_model.id
        assert result.card_id == "CARD001"
    
    async def test_get_by_card_id_not_found(self, card_repository: SqlAlchemyCardRepository):
        """Test getting card by card_id when card doesn't exist"""
        result = await card_repository.get_by_card_id("NONEXISTENT")
        
        assert result is None
    
    async def test_get_by_user_id(self, card_repository: SqlAlchemyCardRepository, sample_card_model: CardModel, sample_user_model: UserModel):
        """Test getting cards by user_id"""
        result = await card_repository.get_by_user_id(sample_user_model.id)
        
        assert len(result) == 1
        assert result[0].id == sample_card_model.id
        assert result[0].user_id == sample_user_model.id
    
    async def test_get_by_user_id_no_cards(self, card_repository: SqlAlchemyCardRepository):
        """Test getting cards by user_id when user has no cards"""
        result = await card_repository.get_by_user_id(999)
        
        assert len(result) == 0
    
    async def test_update_card(self, card_repository: SqlAlchemyCardRepository, sample_card_model: CardModel):
        """Test updating card"""
        # Get the card first
        card = await card_repository.get_by_id(sample_card_model.id)
        assert card is not None
        
        # Update the card
        card.card_type = CardType.VISITOR
        card.status = CardStatus.SUSPENDED
        
        result = await card_repository.update(card)
        
        assert result.card_type == CardType.VISITOR
        assert result.status == CardStatus.SUSPENDED
        assert result.updated_at > card.created_at
    
    async def test_update_card_not_found(self, card_repository: SqlAlchemyCardRepository):
        """Test updating card that doesn't exist"""
        now = datetime.now(UTC).replace(tzinfo=None)
        card = Card(
            id=999,  # Non-existent ID
            card_id="CARD999",
            user_id=1,
            card_type=CardType.EMPLOYEE,
            status=CardStatus.ACTIVE,
            valid_from=now,
            valid_until=None,
            created_at=now,
            updated_at=now,
            use_count=0
        )
        
        with pytest.raises(RepositoryError, match="Card with ID 999 not found"):
            await card_repository.update(card)
    
    async def test_delete_card(self, card_repository: SqlAlchemyCardRepository, sample_card_model: CardModel):
        """Test deleting card"""
        result = await card_repository.delete(sample_card_model.id)
        
        assert result is True
        
        # Verify card is deleted
        deleted_card = await card_repository.get_by_id(sample_card_model.id)
        assert deleted_card is None
    
    async def test_delete_card_not_found(self, card_repository: SqlAlchemyCardRepository):
        """Test deleting card that doesn't exist"""
        result = await card_repository.delete(999)
        
        assert result is False
    
    async def test_list_cards(self, card_repository: SqlAlchemyCardRepository, sample_card_model: CardModel):
        """Test listing cards with pagination"""
        result = await card_repository.list_cards(skip=0, limit=10)
        
        assert len(result) >= 1
        assert any(card.id == sample_card_model.id for card in result)
    
    async def test_list_cards_pagination(self, card_repository: SqlAlchemyCardRepository, db_session: AsyncSession, sample_user_model: UserModel):
        """Test cards pagination"""
        # Create multiple cards for pagination testing
        now = datetime.now(UTC).replace(tzinfo=None)
        for i in range(5):
            card_model = CardModel(
                card_id=f"CARD{i+10}",
                user_id=sample_user_model.id,
                card_type="employee",
                status="active",
                valid_from=now,
                use_count=0
            )
            db_session.add(card_model)
        await db_session.commit()
        
        # Test pagination
        first_page = await card_repository.list_cards(skip=0, limit=3)
        second_page = await card_repository.list_cards(skip=3, limit=3)
        
        assert len(first_page) == 3
        assert len(second_page) >= 1
        
        # Ensure no overlap
        first_page_ids = {card.id for card in first_page}
        second_page_ids = {card.id for card in second_page}
        assert first_page_ids.isdisjoint(second_page_ids)
    
    async def test_get_active_cards(self, card_repository: SqlAlchemyCardRepository, db_session: AsyncSession, sample_user_model: UserModel):
        """Test getting only active cards"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        # Create inactive card
        inactive_card = CardModel(
            card_id="INACTIVE001",
            user_id=sample_user_model.id,
            card_type="employee",
            status="inactive",
            valid_from=now,
            use_count=0
        )
        db_session.add(inactive_card)
        await db_session.commit()
        
        result = await card_repository.get_active_cards()
        
        # Should only return active cards
        assert all(card.status == CardStatus.ACTIVE for card in result)
        assert not any(card.card_id == "INACTIVE001" for card in result)