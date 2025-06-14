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
        """
        Provides a mocked asynchronous database session for testing purposes.
        
        Returns:
            An AsyncMock instance simulating an AsyncSession.
        """
        from unittest.mock import AsyncMock
        session = AsyncMock(spec=AsyncSession)
        return session
    
    @pytest.fixture
    def repository(self, db_session):
        """
        Creates a PermissionRepository instance using the provided database session.
        
        Args:
            db_session: The asynchronous database session to be used by the repository.
        
        Returns:
            A PermissionRepository initialized with the given session.
        """
        return PermissionRepository(db_session)
    
    @pytest.fixture
    def sample_permission(self):
        """
        Creates a sample Permission entity with predefined attributes for testing purposes.
        
        Returns:
            Permission: A Permission instance populated with sample data.
        """
        return Permission(
            id=SAMPLE_CARD_UUID,
            user_id=SAMPLE_CARD_UUID,
            door_id=SAMPLE_CARD_UUID,
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
        """
        Creates a sample PermissionModel instance with predefined attributes for testing purposes.
        
        Returns:
            PermissionModel: A permission model populated with sample data.
        """
        return PermissionModel(
            id=SAMPLE_CARD_UUID,
            user_id=SAMPLE_CARD_UUID,
            door_id=SAMPLE_CARD_UUID,
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
        """
        Tests that a permission is successfully created in the repository.
        
        Verifies that the repository's create method returns a non-None result and that the database session's add, commit, and refresh methods are called once.
        """
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
        """
        Tests that creating a permission raises a RepositoryError and rolls back the transaction when a database error occurs.
        """
        # Arrange
        db_session.commit.side_effect = Exception("Database error")
        db_session.rollback = AsyncMock()
        
        # Act & Assert
        with pytest.raises(RepositoryError, match="Failed to create permission"):
            await repository.create(sample_permission)
        db_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repository, sample_permission_model, db_session):
        """
        Tests that retrieving a permission by ID returns the expected permission when found.
        """
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
        """
        Tests that retrieving a permission by a non-existent ID returns None.
        """
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
        """
        Tests that retrieving a permission by user and door IDs returns the expected permission.
        
        Verifies that the repository returns a permission entity when a matching user and door are found in the database.
        """
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
        """
        Tests that access is granted when a matching permission exists for the given user, door, time, and day.
        """
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
        """
        Tests that check_access returns False when no matching permission exists for the given user, door, time, and day.
        """
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
        """
        Tests that updating a permission via the repository succeeds and commits changes.
        
        Verifies that the repository's update method returns a non-None result and that the session's commit and refresh methods are called when the permission exists.
        """
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
        """
        Tests that updating a non-existent permission raises a RepositoryError.
        """
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
        """
        Tests that deleting an existing permission returns True and commits the transaction.
        """
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
        """
        Tests that deleting a non-existent permission returns False.
        """
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
        """
        Tests that listing permissions returns the expected list of permission entities.
        
        Verifies that the repository's list_permissions method retrieves and returns a list containing the correct permission models when the database session returns results.
        """
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
        """
        Tests that active permissions are successfully retrieved from the repository.
        
        Verifies that the repository returns a list containing only active permission entities when queried.
        """
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
        """
        Tests that the repository raises a RepositoryError when a database execution error occurs.
        """
        # Arrange
        db_session.execute.side_effect = Exception("Database connection error")
        
        # Act & Assert
        with pytest.raises(RepositoryError):
            await repository.get_by_id(1)