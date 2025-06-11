"""
Integration tests for error handling and edge cases.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock
import asyncio

from app.main import app
from app.shared.database.session import get_db
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.models.card import CardModel
from app.infrastructure.database.models.door import DoorModel
from uuid import UUID

class TestErrorHandling:
    """Integration tests for error handling scenarios."""
    TEST_DOOR_ID = UUID("da751b1d-2e7b-402c-b7ad-6f50c8cb6fe5")
    @pytest.fixture
    async def client(self):
        """HTTP client for testing."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.fixture
    async def db_session(self):
        """Database session for testing."""
        async for session in get_db():
            yield session
            break
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, client: AsyncClient):
        """Test API behavior when database is unavailable."""
        with patch('app.shared.database.session.get_db') as mock_get_db:
            # Simulate database connection error
            async def failing_db():
                raise Exception("Database connection failed")
            
            mock_get_db.return_value = failing_db()
            
            response = await client.post(
                "/api/v1/access/validate",
                json={"card_id": "TEST123", "door_id": self.TEST_DOOR_ID}
            )
            
            # Should return 500 internal server error
            assert response.status_code == 500
    
    @pytest.mark.asyncio
    async def test_malformed_json_request(self, client: AsyncClient):
        """Test API response to malformed JSON."""
        response = await client.post(
            "/api/v1/access/validate",
            content="invalid json content",
            headers={"content-type": "application/json"}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_extremely_large_request(self, client: AsyncClient):
        """Test API response to extremely large request data."""
        large_card_id = "X" * 10000  # Very large card ID
        
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": large_card_id, "door_id": self.TEST_DOOR_ID}
        )
        
        # Should be rejected due to validation
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_special_characters_in_card_id(self, client: AsyncClient):
        """Test handling of special characters in card IDs."""
        special_chars_cards = [
            "card@#$%",
            "card with spaces",
            "card\nwith\nnewlines",
            "card\x00with\x00nulls",
            "card🎯with🎯emojis"
        ]
        
        for card_id in special_chars_cards:
            response = await client.post(
                "/api/v1/access/validate",
                json={"card_id": card_id, "door_id": self.TEST_DOOR_ID}
            )
            
            # Should return 404 (card not found) or 422 (validation error)
            assert response.status_code in [404, 422]
    
    @pytest.mark.asyncio
    async def test_sql_injection_attempts(self, client: AsyncClient):
        """Test protection against SQL injection attempts."""
        sql_injection_attempts = [
            "'; DROP TABLE cards; --",
            "1' OR '1'='1",
            "1'; DELETE FROM permissions; --",
            "UNION SELECT * FROM users",
            "1' UNION SELECT password FROM users WHERE '1'='1"
        ]
        
        for injection_attempt in sql_injection_attempts:
            response = await client.post(
                "/api/v1/access/validate",
                json={"card_id": injection_attempt, "door_id": self.TEST_DOOR_ID}
            )
            
            # Should safely return 404 (not found) without executing injection
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_concurrent_card_operations(self, client: AsyncClient, db_session: AsyncSession):
        """Test concurrent operations on the same card."""
        import asyncio
        
        # Create test user and card
        user = UserModel(
            email="test@concurrent.com",
            hashed_password="hashed",
            full_name="Test User",
            roles=["user"],
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        card = CardModel(
            user_id=user.id,
            card_id="CONCURRENT001",
            card_type="employee",
            status="active",
            valid_from=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(card)
        await db_session.commit()
        
        door = DoorModel(
            name="Concurrent Test Door",
            location="Test Location",
            security_level="low",
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(door)
        await db_session.commit()
        await db_session.refresh(door)
        
        # Make multiple concurrent access validation requests
        async def validate_access():
            return await client.post(
                "/api/v1/access/validate",
                json={"card_id": "CONCURRENT001", "door_id": door.id}
            )
        
        # Execute 10 concurrent requests
        tasks = [validate_access() for _ in range(10)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All responses should be consistent (either all success or all failure)
        status_codes = [r.status_code if hasattr(r, 'status_code') else 500 for r in responses]
        
        # Should not have any 500 errors from race conditions
        assert 500 not in status_codes
    
    @pytest.mark.asyncio
    async def test_missing_content_type_header(self, client: AsyncClient):
        """Test API response when Content-Type header is missing."""
        response = await client.post(
            "/api/v1/access/validate",
            content=f'{"card_id": "TEST123", "door_id": {self.TEST_DOOR_ID}}'
            # No Content-Type header
        )
        
        # FastAPI should still handle it or return appropriate error
        assert response.status_code in [200, 400, 404, 422]
    
    @pytest.mark.asyncio
    async def test_unsupported_http_methods(self, client: AsyncClient):
        """Test unsupported HTTP methods on access validation endpoint."""
        # Test GET (should be 405 Method Not Allowed)
        response = await client.get("/api/v1/access/validate")
        assert response.status_code == 405
        
        # Test PUT (should be 405 Method Not Allowed)
        response = await client.put(
            "/api/v1/access/validate",
            json={"card_id": "TEST123", "door_id": {self.TEST_DOOR_ID}}
        )
        assert response.status_code == 405
        
        # Test DELETE (should be 405 Method Not Allowed)
        response = await client.delete("/api/v1/access/validate")
        assert response.status_code == 405
    
    @pytest.mark.asyncio
    async def test_extremely_large_door_id(self, client: AsyncClient):
        """Test handling of extremely large door IDs."""
        large_door_id = 2**63 - 1  # Maximum 64-bit integer
        
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": "TEST123", "door_id": large_door_id}
        )
        
        # Should return 404 (door not found) not 500 (overflow error)
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_negative_door_id(self, client: AsyncClient):
        """Test handling of negative door IDs."""
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": "TEST123", "door_id": -1}
        )
        
        # Should be rejected by validation
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_zero_door_id(self, client: AsyncClient):
        """Test handling of zero door ID."""
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": "TEST123", "door_id": 0}
        )
        
        # Should be rejected by validation (door_id must be > 0)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_float_door_id(self, client: AsyncClient):
        """Test handling of float door IDs."""
        response = await client.post(
            "/api/v1/access/validate",
            json={f'"card_id": "TEST123", "door_id": {self.TEST_DOOR_ID}.5'}
        )
        
        # Should be rejected by validation or converted to int
        assert response.status_code in [404, 422]  # Either validation error or not found
    
    @pytest.mark.asyncio
    async def test_null_values_in_request(self, client: AsyncClient):
        """Test handling of null values in request."""
        # Null card_id
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": None, "door_id": {self.TEST_DOOR_ID}}
        )
        assert response.status_code == 422
        
        # Null door_id
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": "TEST123", "door_id": None}
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_unicode_handling(self, client: AsyncClient):
        """Test handling of Unicode characters in requests."""
        unicode_card_ids = [
            "测试卡片123",  # Chinese characters
            "κάρτα123",    # Greek characters
            "カード123",    # Japanese characters
            "🔑KEY123🔑",  # Emoji characters
        ]
        
        for card_id in unicode_card_ids:
            response = await client.post(
                "/api/v1/access/validate",
                json={"card_id": card_id, "door_id": {self.TEST_DOOR_ID}}
            )
            
            # Should handle Unicode gracefully
            assert response.status_code in [404, 422]  # Not found or validation error
            
            # Response should be valid JSON
            assert response.json() is not None
    
    @pytest.mark.asyncio
    async def test_repository_timeout_simulation(self, client: AsyncClient):
        """Test behavior when repository operations timeout."""
        with patch('app.infrastructure.persistence.adapters.card_repository.SqlAlchemyCardRepository.get_by_card_id') as mock_get_card:
            # Simulate timeout
            mock_get_card.side_effect = asyncio.TimeoutError("Database timeout")
            
            response = await client.post(
                "/api/v1/access/validate",
                json={"card_id": "TEST123", "door_id": {self.TEST_DOOR_ID}}
            )
            
            # Should return 500 internal server error
            assert response.status_code == 500
    
    @pytest.mark.asyncio
    async def test_invalid_authentication_tokens(self, client: AsyncClient):
        """Test handling of invalid authentication tokens."""
        invalid_tokens = [
            "Bearer invalid_token",
            "Bearer ",
            "InvalidFormat token",
            "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature",
            "",
        ]
        
        for token in invalid_tokens:
            headers = {"Authorization": token} if token else {}
            
            response = await client.get("/api/v1/cards/", headers=headers)
            
            # Should return 401 Unauthorized
            assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_rate_limiting_simulation(self, client: AsyncClient):
        """Test rapid successive requests (basic rate limiting test)."""
        # Make 50 rapid requests
        responses = []
        for i in range(50):
            response = await client.post(
                "/api/v1/access/validate",
                json={"card_id": f"RAPID{i:03d}", "door_id": {self.TEST_DOOR_ID}}
            )
            responses.append(response)
        
        # All should be handled gracefully (no 500 errors from overload)
        status_codes = [r.status_code for r in responses]
        assert 500 not in status_codes
        
        # Most should be 404 (not found) since these are test cards
        assert status_codes.count(404) > 40