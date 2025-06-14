import pytest
from fastapi.testclient import TestClient

class TestPermissionsAPIBasic:
    """Basic integration tests for Permissions API endpoints - verify routes exist and authentication works"""
    
    @pytest.fixture
    def client(self):
        """
        Provides a test HTTP client for the FastAPI application.
        
        Returns:
            A TestClient instance for making HTTP requests to the app during tests.
        """
        from app.main import app
        return TestClient(app)

    def test_permissions_endpoints_require_auth(self, client):
        """
        Verifies that all Permissions API endpoints return HTTP 401 Unauthorized when accessed without authentication.
        
        This test ensures that unauthenticated requests to the main Permissions API routes are properly rejected, enforcing authentication requirements.
        """
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
        """
        Verifies that all main Permissions API endpoints are present in the OpenAPI specification.
        
        Sends a request to the OpenAPI JSON endpoint and asserts the existence of key permissions-related paths to ensure the API is properly documented.
        """
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
        """
        Verifies that the Permissions API endpoints are tagged as "Permissions" in the OpenAPI specification.
        
        Ensures the OpenAPI JSON includes a tag named "Permissions" to categorize the Permissions API.
        """
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        tags = [tag["name"] for tag in openapi_spec.get("tags", [])]
        assert "Permissions" in tags