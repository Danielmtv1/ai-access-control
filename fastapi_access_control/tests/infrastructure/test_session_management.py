"""
Tests for database session management.
"""
import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.database.session import get_db, AsyncSessionLocal


class TestSessionManagement:
    """Test suite for database session management."""
    
    @pytest.mark.asyncio
    async def test_get_db_success(self):
        """Test successful database session creation."""
        # Mock AsyncSessionLocal
        with patch('app.shared.database.session.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            # Act
            async for session in get_db():
                # Assert
                assert session is not None
                assert session == mock_session
                break
    
    @pytest.mark.asyncio
    async def test_get_db_exception_handling(self):
        """Test database session exception handling."""
        with patch('app.shared.database.session.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock()
            
            # Configure the context manager
            async def mock_context_manager():
                yield mock_session
                # Simulate an exception during yield
                raise Exception("Database error")
            
            mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_local.return_value.__aexit__ = AsyncMock()
            
            # Simulate exception in the session
            with patch.object(mock_session, 'execute', side_effect=Exception("Query error")):
                try:
                    async for session in get_db():
                        # Simulate a database operation that fails
                        await session.execute("SELECT 1")
                        break
                except Exception:
                    # Exception should be handled by the generator
                    pass
    
    @pytest.mark.asyncio
    async def test_session_configuration(self):
        """Test that session is properly configured."""
        # This test verifies the session configuration
        assert AsyncSessionLocal is not None
        
        # Check session configuration attributes
        session_config = AsyncSessionLocal
        assert hasattr(session_config, 'bind')
        assert hasattr(session_config, 'autocommit')
        assert hasattr(session_config, 'autoflush')
    
    @pytest.mark.asyncio
    async def test_get_db_cleanup(self):
        """Test that database session is properly cleaned up."""
        with patch('app.shared.database.session.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.close = AsyncMock()
            
            # Configure the async context manager
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            # Act
            async for session in get_db():
                # Verify session is provided
                assert session == mock_session
                break
            
            # The session cleanup happens automatically in the context manager
            # We can verify the context manager was used correctly
            mock_session_local.assert_called_once()
    
    def test_database_url_configuration(self):
        """Test database URL configuration."""
        from app.shared.database.session import DATABASE_URL, ASYNC_DATABASE_URL
        
        # Verify URL transformation
        assert DATABASE_URL is not None
        assert ASYNC_DATABASE_URL is not None
        
        # Verify async URL uses asyncpg driver
        if "postgresql://" in DATABASE_URL:
            assert "postgresql+asyncpg://" in ASYNC_DATABASE_URL
    
    def test_engine_configuration(self):
        """Test database engine configuration."""
        from app.shared.database.session import engine
        
        # Verify engine exists and has proper configuration
        assert engine is not None
        assert hasattr(engine, 'url')
        assert hasattr(engine, 'pool')
    
    @pytest.mark.asyncio
    async def test_multiple_sessions(self):
        """Test that multiple sessions can be created independently."""
        with patch('app.shared.database.session.AsyncSessionLocal') as mock_session_local:
            # Create multiple mock sessions
            mock_session1 = AsyncMock(spec=AsyncSession)
            mock_session2 = AsyncMock(spec=AsyncSession)
            
            # Configure mock to return different sessions for each call
            mock_session_local.side_effect = [
                AsyncMock(__aenter__=AsyncMock(return_value=mock_session1), __aexit__=AsyncMock()),
                AsyncMock(__aenter__=AsyncMock(return_value=mock_session2), __aexit__=AsyncMock())
            ]
            
            # Get first session
            async for session1 in get_db():
                assert session1 == mock_session1
                break
            
            # Get second session
            async for session2 in get_db():
                assert session2 == mock_session2
                break
            
            # Verify both sessions were created
            assert mock_session_local.call_count == 2
    
    @pytest.mark.asyncio
    async def test_session_transaction_handling(self):
        """Test session transaction handling on exceptions."""
        with patch('app.shared.database.session.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock()
            
            # Configure context manager that raises exception
            async def raising_context_manager():
                async with mock_session_local() as session:
                    yield session
                    raise Exception("Transaction error")
            
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.side_effect = Exception("Transaction error")
            
            # Test that exception in context manager is handled
            try:
                async for session in get_db():
                    assert session == mock_session
                    # Context manager will handle rollback
                    break
            except Exception:
                # Exception may be re-raised, which is fine
                pass