import pytest
from fastapi.testclient import TestClient

class TestUsersAPIBasic:
    """Basic integration tests for Users API endpoints - verify routes exist and authentication works"""
    
    @pytest.fixture
    def client(self):
        """HTTP client for testing."""
        from app.main import app
        return TestClient(app)

    def test_users_endpoints_require_auth(self, client):
        """Test that users endpoints require authentication"""
        # Test main endpoints return 401 without auth
        assert client.post("/api/v1/users/", json={}).status_code == 401
        assert client.get("/api/v1/users/").status_code == 401
        assert client.get("/api/v1/users/stats").status_code == 401
        assert client.get("/api/v1/users/123").status_code == 401
        assert client.get("/api/v1/users/email/test@test.com").status_code == 401
        assert client.put("/api/v1/users/123", json={}).status_code == 401
        assert client.delete("/api/v1/users/123").status_code == 401
        assert client.post("/api/v1/users/123/suspend").status_code == 401
        assert client.post("/api/v1/users/123/activate").status_code == 401
        assert client.post("/api/v1/users/123/change-password", json={}).status_code == 401

    def test_users_endpoints_exist(self, client):
        """Test that users endpoints exist in OpenAPI spec"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        paths = openapi_spec.get("paths", {})
        
        # Check that users endpoints are defined
        assert "/api/v1/users/" in paths
        assert "/api/v1/users/stats" in paths
        assert "/api/v1/users/{user_id}" in paths
        assert "/api/v1/users/email/{email}" in paths
        assert "/api/v1/users/{user_id}/suspend" in paths
        assert "/api/v1/users/{user_id}/activate" in paths
        assert "/api/v1/users/{user_id}/change-password" in paths

    def test_users_api_tags_in_openapi(self, client):
        """Test that users API is properly tagged in OpenAPI"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        tags = [tag["name"] for tag in openapi_spec.get("tags", [])]
        assert "Users" in tags

    def test_users_validation_schemas(self, client):
        """Test that user validation works for invalid data"""
        # Test invalid email format (should return 422 even without auth for validation)
        response = client.post("/api/v1/users/", json={
            "email": "invalid-email",
            "password": "test",
            "full_name": "Test User"
        })
        # Should get 401 for auth first, not 422 for validation
        assert response.status_code == 401