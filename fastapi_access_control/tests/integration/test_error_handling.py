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
from tests.conftest import SAMPLE_USER_UUID, SAMPLE_CARD_UUID, SAMPLE_DOOR_UUID

class TestErrorHandling:
    """Integration tests for error handling scenarios."""
    @pytest.fixture
    async def client(self):
        """
        Provides an asynchronous HTTP client for integration tests.
        
        Yields:
            An instance of AsyncClient configured for the FastAPI app.
        """
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.fixture
    async def db_session(self):
        """
        Yields an asynchronous database session for use in integration tests.
        
        This fixture provides a single session from the application's database session generator.
        """
        async for session in get_db():
            yield session
            break
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, client: AsyncClient):
        """
        Tests that the access validation API returns HTTP 500 when the database connection fails.
        """
        with patch('app.shared.database.session.get_db') as mock_get_db:
            # Simulate database connection error
            async def failing_db():
                """
                Simulates a database connection failure by raising an exception.
                
                Raises:
                    Exception: Always raised to indicate a failed database connection.
                """
                raise Exception("Database connection failed")
            
            mock_get_db.return_value = failing_db()
            
            response = await client.post(
                "/api/v1/access/validate",
                json={"card_id": "TEST123", "door_id": str(SAMPLE_DOOR_UUID)}
            )
            
            # Should return 500 internal server error
            assert response.status_code == 500
    
    @pytest.mark.asyncio
    async def test_malformed_json_request(self, client: AsyncClient):
        """
        Tests that the API returns HTTP 422 when receiving a malformed JSON payload.
        """
        response = await client.post(
            "/api/v1/access/validate",
            content="invalid json content",
            headers={"content-type": "application/json"}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_extremely_large_request(self, client: AsyncClient):
        """
        Tests that the API rejects requests with an excessively large `card_id` value.
        
        Sends a request to the access validation endpoint with a `card_id` string of 10,000 characters and verifies that the API responds with HTTP 422 Unprocessable Entity due to input validation.
        """
        large_card_id = "X" * 10000  # Very large card ID
        
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": large_card_id, "door_id": str(SAMPLE_DOOR_UUID)}
        )
        
        # Should be rejected due to validation
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_special_characters_in_card_id(self, client: AsyncClient):
        """
        Tests API response to card IDs containing special characters.
        
        Sends access validation requests with card IDs that include symbols, whitespace, control characters, null bytes, and emojis, verifying the API returns either 404 (not found) or 422 (validation error).
        """
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
                json={"card_id": card_id, "door_id": str(SAMPLE_DOOR_UUID)}
            )
            
            # Should return 404 (card not found) or 422 (validation error)
            assert response.status_code in [404, 422]
    
    @pytest.mark.asyncio
    async def test_sql_injection_attempts(self, client: AsyncClient):
        """
        Verifies that the access validation endpoint safely handles SQL injection attempts in the card ID field.
        
        Sends typical SQL injection payloads as `card_id` and asserts the API responds with HTTP 404 and an appropriate error message, confirming no injection is executed.
        """
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
                json={"card_id": injection_attempt, "door_id": str(SAMPLE_DOOR_UUID)}
            )
            
            # Should safely return 404 (not found) without executing injection
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_concurrent_card_operations(self, client: AsyncClient, db_session: AsyncSession):
        """
        Verifies that concurrent access validation requests for the same card and door do not cause server errors.
        
        Creates a user, card, and door in the database, then issues 10 simultaneous POST requests to the access validation endpoint using the same card and door. Asserts that no HTTP 500 errors occur, ensuring the API handles concurrent operations safely.
        """
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
            """
            Sends an asynchronous POST request to the access validation endpoint with a specified card and door ID.
            
            Returns:
                The HTTP response from the access validation API.
            """
            return await client.post(
                "/api/v1/access/validate",
                json={"card_id": "CONCURRENT001", "door_id": str(door.id)}
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
        """
        Tests the API's behavior when a POST request is sent without a Content-Type header.
        
        Sends a raw JSON payload to the access validation endpoint without specifying the Content-Type header and asserts that the response status code is one of the expected values, indicating graceful handling or appropriate error reporting.
        """
        response = await client.post(
            "/api/v1/access/validate",
            content=f'{"card_id": "TEST123", "door_id": "{SAMPLE_DOOR_UUID}"}'
            # No Content-Type header
        )
        
        # FastAPI should still handle it or return appropriate error
        assert response.status_code in [200, 400, 404, 422]
    
    @pytest.mark.asyncio
    async def test_unsupported_http_methods(self, client: AsyncClient):
        """
        Verifies that the access validation endpoint rejects unsupported HTTP methods.
        
        Sends GET, PUT, and DELETE requests to the POST-only endpoint and asserts that each returns HTTP 405 Method Not Allowed.
        """
        # Test GET (should be 405 Method Not Allowed)
        response = await client.get("/api/v1/access/validate")
        assert response.status_code == 405
        
        # Test PUT (should be 405 Method Not Allowed)
        response = await client.put(
            "/api/v1/access/validate",
            json={"card_id": "TEST123", "door_id": str(SAMPLE_DOOR_UUID)}
        )
        assert response.status_code == 405
        
        # Test DELETE (should be 405 Method Not Allowed)
        response = await client.delete("/api/v1/access/validate")
        assert response.status_code == 405
    
    @pytest.mark.asyncio
    async def test_extremely_large_door_id(self, client: AsyncClient):
        """
        Tests that the API returns a 422 validation error when an invalid UUID string is provided as the door ID.
        """
        invalid_door_uuid = "invalid-uuid-format"
        
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": "TEST123", "door_id": invalid_door_uuid}
        )
        
        # Should return 422 (validation error) for invalid UUID format
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_negative_door_id(self, client: AsyncClient):
        """
        Tests that providing an invalid UUID string as the door ID results in a 422 Unprocessable Entity response.
        """
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": "TEST123", "door_id": "negative-invalid"}
        )
        
        # Should be rejected by UUID validation
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_zero_door_id(self, client: AsyncClient):
        """
        Tests the API's response when a nil UUID is provided as the door ID.
        
        Sends an access validation request with a valid card ID and a door ID set to the nil UUID. Expects a 404 Not Found response, indicating the door does not exist.
        """
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": "TEST123", "door_id": "00000000-0000-0000-0000-000000000000"}
        )
        
        # Should return 404 (door not found) for nil UUID
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_float_door_id(self, client: AsyncClient):
        """
        Tests that providing a float-like string as a door ID results in a 422 validation error.
        """
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": "TEST123", "door_id": "invalid.5"}
        )
        
        # Should be rejected by UUID validation
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_null_values_in_request(self, client: AsyncClient):
        """
        Tests that the access validation endpoint returns HTTP 422 when null values are provided for card_id or door_id in the request payload.
        """
        # Null card_id
        response = await client.post(
            "/api/v1/access/validate",
            json={"card_id": None, "door_id": str(SAMPLE_DOOR_UUID)}
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
        """
        Tests the API's handling of Unicode characters in the `card_id` field during access validation.
        
        Sends requests with various Unicode `card_id` values (including Chinese, Greek, Japanese, and emoji) to the access validation endpoint and asserts that the API responds with either HTTP 404 or 422, and always returns a valid JSON response.
        """
        unicode_card_ids = [
            "测试卡片123",  # Chinese characters
            "κάρτα123",    # Greek characters
            "カード123",    # Japanese characters
            "🔑KEY123🔑",  # Emoji characters
        ]
        
        for card_id in unicode_card_ids:
            response = await client.post(
                "/api/v1/access/validate",
                json={"card_id": card_id, "door_id": str(SAMPLE_DOOR_UUID)}
            )
            
            # Should handle Unicode gracefully
            assert response.status_code in [404, 422]  # Not found or validation error
            
            # Response should be valid JSON
            assert response.json() is not None
    
    @pytest.mark.asyncio
    async def test_repository_timeout_simulation(self, client: AsyncClient):
        """
        Simulates a repository timeout during access validation and verifies the API returns HTTP 500.
        
        This test patches the card repository to raise an asyncio.TimeoutError, mimicking a backend timeout scenario, and asserts that the API responds with a 500 Internal Server Error.
        """
        with patch('app.infrastructure.persistence.adapters.card_repository.SqlAlchemyCardRepository.get_by_card_id') as mock_get_card:
            # Simulate timeout
            mock_get_card.side_effect = asyncio.TimeoutError("Database timeout")
            
            response = await client.post(
                "/api/v1/access/validate",
                json={"card_id": "TEST123", "door_id": str(SAMPLE_DOOR_UUID)}
            )
            
            # Should return 500 internal server error
            assert response.status_code == 500
    
    @pytest.mark.asyncio
    async def test_invalid_authentication_tokens(self, client: AsyncClient):
        """
        Verifies that the API returns 401 Unauthorized for requests with invalid or malformed authentication tokens.
        
        Sends GET requests to the protected cards endpoint using various invalid `Authorization` headers and asserts that unauthorized access is correctly rejected.
        """
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
        """
        Simulates rapid successive access validation requests to test API rate limiting and robustness.
        
        Sends 50 rapid POST requests with unique card IDs to the access validation endpoint and asserts that no internal server errors (HTTP 500) occur, and that the majority of responses are HTTP 404 (not found).
        """
        # Make 50 rapid requests
        responses = []
        for i in range(50):
            response = await client.post(
                "/api/v1/access/validate",
                json={"card_id": f"RAPID{i:03d}", "door_id": str(SAMPLE_DOOR_UUID)}
            )
            responses.append(response)
        
        # All should be handled gracefully (no 500 errors from overload)
        status_codes = [r.status_code for r in responses]
        assert 500 not in status_codes
        
        # Most should be 404 (not found) since these are test cards
        assert status_codes.count(404) > 40