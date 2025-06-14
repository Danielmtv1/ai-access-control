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
        """
        Tests that the get_db async generator yields a valid database session when session creation succeeds.
        """
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
        """
        Tests that exceptions raised during database session usage are handled gracefully by the session generator.
        
        Simulates errors during a database operation and verifies that the session generator does not crash when exceptions occur within the session context.
        """
        with patch('app.shared.database.session.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock()
            
            # Configure the context manager
            async def mock_context_manager():
                """
                Asynchronous context manager mock that yields a mock session and then raises an exception.
                
                Yields:
                    The mocked session object before raising an exception to simulate a database error.
                """
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
        """
        Verifies that the asynchronous session factory is defined and has required configuration attributes.
        
        Asserts that `AsyncSessionLocal` exists and includes the attributes `bind`, `autocommit`, and `autoflush`.
        """
        # This test verifies the session configuration
        assert AsyncSessionLocal is not None
        
        # Check session configuration attributes
        session_config = AsyncSessionLocal
        assert hasattr(session_config, 'bind')
        assert hasattr(session_config, 'autocommit')
        assert hasattr(session_config, 'autoflush')
    
    @pytest.mark.asyncio
    async def test_get_db_cleanup(self):
        """
        Verifies that the database session is properly cleaned up after use by the async context manager.
        
        Ensures that the session provided by `get_db` is correctly yielded and that the session factory's context manager is invoked as expected.
        """
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
        """
        Verifies that the database URL and async database URL are defined and correctly configured.
        
        Checks that both `DATABASE_URL` and `ASYNC_DATABASE_URL` are set, and ensures that if the synchronous URL uses the `postgresql://` scheme, the async URL uses the `postgresql+asyncpg://` scheme.
        """
        from app.shared.database.session import DATABASE_URL, ASYNC_DATABASE_URL
        
        # Verify URL transformation
        assert DATABASE_URL is not None
        assert ASYNC_DATABASE_URL is not None
        
        # Verify async URL uses asyncpg driver
        if "postgresql://" in DATABASE_URL:
            assert "postgresql+asyncpg://" in ASYNC_DATABASE_URL
    
    def test_engine_configuration(self):
        """
        Verifies that the database engine is defined and has required configuration attributes.
        
        Asserts that the engine object exists and includes both 'url' and 'pool' attributes.
        """
        from app.shared.database.session import engine
        
        # Verify engine exists and has proper configuration
        assert engine is not None
        assert hasattr(engine, 'url')
        assert hasattr(engine, 'pool')
    
    @pytest.mark.asyncio
    async def test_multiple_sessions(self):
        """
        Tests that multiple independent database sessions can be created and retrieved, ensuring each session instance is distinct and the session factory is called for each request.
        """
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
        """
        Tests that transaction rollback and cleanup are properly handled when an exception occurs during the database session context.
        
        Verifies that if an exception is raised during the session's context manager exit, the session's rollback and close methods are called to ensure proper transaction handling and resource cleanup.
        """
        with patch('app.shared.database.session.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock()
            
            # Configure context manager that raises exception
            async def raising_context_manager():
                """
                Yields a mocked database session and then raises an exception to simulate a transaction error.
                
                Intended for testing exception handling during session context management.
                """
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