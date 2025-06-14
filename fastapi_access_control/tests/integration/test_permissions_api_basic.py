import pytest
from fastapi.testclient import TestClient

class TestPermissionsAPIBasic:
    """Basic integration tests for Permissions API endpoints - verify routes exist and authentication works"""
    
    @pytest.fixture
    def client(self):
        """HTTP client for testing."""
        from app.main import app
        return TestClient(app)

    def test_permissions_endpoints_require_auth(self, client):
        """Test that permissions endpoints require authentication"""
        # Test main endpoints return 401 without auth
        assert client.post("/api/v1/permissions/", json={}).status_code == 401
        assert client.get("/api/v1/permissions/").status_code == 401
        assert client.get("/api/v1/permissions/123").status_code == 401
        assert client.put("/api/v1/permissions/123", json={}).status_code == 401
        assert client.delete("/api/v1/permissions/123").status_code == 401
        assert client.post("/api/v1/permissions/123/revoke").status_code == 401
        assert client.get("/api/v1/permissions/users/123").status_code == 401
        assert client.get("/api/v1/permissions/doors/123").status_code == 401
        assert client.post("/api/v1/permissions/bulk", json={}).status_code == 401

    def test_permissions_endpoints_exist(self, client):
        """Test that permissions endpoints exist in OpenAPI spec"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        paths = openapi_spec.get("paths", {})
        
        # Check that permissions endpoints are defined
        assert "/api/v1/permissions/" in paths
        assert "/api/v1/permissions/{permission_id}" in paths
        assert "/api/v1/permissions/{permission_id}/revoke" in paths
        assert "/api/v1/permissions/users/{user_id}" in paths
        assert "/api/v1/permissions/doors/{door_id}" in paths
        assert "/api/v1/permissions/bulk" in paths

    def test_permissions_api_tags_in_openapi(self, client):
        """Test that permissions API is properly tagged in OpenAPI"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        tags = [tag["name"] for tag in openapi_spec.get("tags", [])]
        assert "Permissions" in tags