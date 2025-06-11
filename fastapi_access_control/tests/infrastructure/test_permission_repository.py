"""
Tests for permission repository implementation.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, time

from app.infrastructure.persistence.adapters.permission_repository import PermissionRepository
from app.domain.entities.permission import Permission, PermissionStatus
from app.infrastructure.database.models.permission import PermissionModel
from app.domain.exceptions import RepositoryError


class TestPermissionRepository:
    """Test suite for PermissionRepository."""
    
    @pytest.fixture
    async def db_session(self):
        """Mock database session."""
        from unittest.mock import AsyncMock
        session = AsyncMock(spec=AsyncSession)
        return session
    
    @pytest.fixture
    def repository(self, db_session):
        """Create PermissionRepository instance."""
        return PermissionRepository(db_session)
    
    @pytest.fixture
    def sample_permission(self):
        """Sample permission entity."""
        return Permission(
            id=1,
            user_id=1,
            door_id=1,
            card_number="TEST123",
            status=PermissionStatus.ACTIVE,
            valid_from=time(8, 0),
            valid_until=time(18, 0),
            days_of_week=["mon", "tue", "wed", "thu", "fri"],
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def sample_permission_model(self):
        """Sample permission database model."""
        return PermissionModel(
            id=1,
            user_id=1,
            door_id=1,
            card_number="TEST123",
            status="active",
            valid_from=time(8, 0),
            valid_until=time(18, 0),
            days_of_week=["mon", "tue", "wed", "thu", "fri"],
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @pytest.mark.asyncio
    async def test_create_permission_success(self, repository, sample_permission, db_session):
        """Test successful permission creation."""
        # Arrange
        db_session.commit = AsyncMock()
        db_session.refresh = AsyncMock()
        
        # Act
        result = await repository.create(sample_permission)
        
        # Assert
        assert result is not None
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_permission_error(self, repository, sample_permission, db_session):
        """Test permission creation with database error."""
        # Arrange
        db_session.commit.side_effect = Exception("Database error")
        db_session.rollback = AsyncMock()
        
        # Act & Assert
        with pytest.raises(RepositoryError, match="Failed to create permission"):
            await repository.create(sample_permission)
        db_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repository, sample_permission_model, db_session):
        """Test successful get permission by ID."""
        # Arrange
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_permission_model
        db_session.execute.return_value = mock_result
        
        # Act
        result = await repository.get_by_id(1)
        
        # Assert
        assert result is not None
        assert result.id == 1
        db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, db_session):
        """Test get permission by ID when not found."""
        # Arrange
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_session.execute.return_value = mock_result
        
        # Act
        result = await repository.get_by_id(999)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_by_user_and_door_success(self, repository, sample_permission_model, db_session):
        """Test successful get permission by user and door."""
        # Arrange
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_permission_model
        db_session.execute.return_value = mock_result
        
        # Act
        result = await repository.get_by_user_and_door(1, 1)
        
        # Assert
        assert result is not None
        assert result.user_id == 1
        assert result.door_id == 1
    
    @pytest.mark.asyncio
    async def test_check_access_with_permission(self, repository, sample_permission_model, db_session):
        """Test check access when permission exists."""
        # Arrange
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_permission_model
        db_session.execute.return_value = mock_result
        
        # Act
        result = await repository.check_access(1, 1, time(10, 0), "mon")
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_access_no_permission(self, repository, db_session):
        """Test check access when no permission exists."""
        # Arrange
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_session.execute.return_value = mock_result
        
        # Act
        result = await repository.check_access(1, 1, time(10, 0), "mon")
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_permission_success(self, repository, sample_permission, sample_permission_model, db_session):
        """Test successful permission update."""
        # Arrange
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_permission_model
        db_session.execute.return_value = mock_result
        db_session.commit = AsyncMock()
        db_session.refresh = AsyncMock()
        
        # Act
        result = await repository.update(sample_permission)
        
        # Assert
        assert result is not None
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_permission_not_found(self, repository, sample_permission, db_session):
        """Test update permission when not found."""
        # Arrange
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_session.execute.return_value = mock_result
        
        # Act & Assert
        with pytest.raises(RepositoryError, match="not found"):
            await repository.update(sample_permission)
    
    @pytest.mark.asyncio
    async def test_delete_permission_success(self, repository, sample_permission_model, db_session):
        """Test successful permission deletion."""
        # Arrange
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_permission_model
        db_session.execute.return_value = mock_result
        db_session.delete = AsyncMock()
        db_session.commit = AsyncMock()
        
        # Act
        result = await repository.delete(1)
        
        # Assert
        assert result is True
        db_session.delete.assert_called_once()
        db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_permission_not_found(self, repository, db_session):
        """Test delete permission when not found."""
        # Arrange
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_session.execute.return_value = mock_result
        
        # Act
        result = await repository.delete(999)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_list_permissions_success(self, repository, sample_permission_model, db_session):
        """Test successful permissions listing."""
        # Arrange
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_permission_model]
        db_session.execute.return_value = mock_result
        
        # Act
        result = await repository.list_permissions(skip=0, limit=10)
        
        # Assert
        assert len(result) == 1
        assert result[0].id == 1
    
    @pytest.mark.asyncio
    async def test_get_active_permissions_success(self, repository, sample_permission_model, db_session):
        """Test successful active permissions retrieval."""
        # Arrange
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_permission_model]
        db_session.execute.return_value = mock_result
        
        # Act
        result = await repository.get_active_permissions()
        
        # Assert
        assert len(result) == 1
        assert result[0].is_active is True
    
    @pytest.mark.asyncio
    async def test_repository_error_handling(self, repository, db_session):
        """Test repository error handling."""
        # Arrange
        db_session.execute.side_effect = Exception("Database connection error")
        
        # Act & Assert
        with pytest.raises(RepositoryError):
            await repository.get_by_id(1)