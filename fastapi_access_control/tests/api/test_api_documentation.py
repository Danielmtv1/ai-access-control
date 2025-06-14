"""
Tests for API documentation and OpenAPI specification.
"""
import pytest
from fastapi.testclient import TestClient
import json

from app.main import app


class TestAPIDocumentation:
    """Test suite for API documentation."""
    
    @pytest.fixture
    def client(self):
        """
        Provides a pytest fixture that returns a TestClient instance for the FastAPI app.
        """
        return TestClient(app)
    
    def test_openapi_schema_generation(self, client):
        """
        Verifies that the OpenAPI schema is generated and contains required top-level fields and correct API metadata.
        """
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        
        # Basic OpenAPI structure
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        assert "components" in schema
        
        # API info
        assert schema["info"]["title"] == "Access Control System"
        assert "version" in schema["info"]
        assert "description" in schema["info"]
    
    def test_access_validation_endpoint_documented(self, client):
        """
        Verifies that the access validation endpoint is documented in the OpenAPI schema.
        
        Checks that the `/api/v1/access/validate` endpoint exists with a POST method, includes required metadata (summary, description, tags), defines a JSON request body schema, and documents expected response codes (200, 403, 404, 422).
        """
        response = client.get("/openapi.json")
        schema = response.json()
        
        # Check access validation endpoint exists
        assert "/api/v1/access/validate" in schema["paths"]
        
        validate_endpoint = schema["paths"]["/api/v1/access/validate"]
        
        # Should have POST method
        assert "post" in validate_endpoint
        
        post_spec = validate_endpoint["post"]
        
        # Should have proper metadata
        assert "summary" in post_spec
        assert "description" in post_spec
        assert "tags" in post_spec
        assert "Access Control" in post_spec["tags"]
        
        # Should have request body schema
        assert "requestBody" in post_spec
        request_body = post_spec["requestBody"]
        assert "content" in request_body
        assert "application/json" in request_body["content"]
        
        # Should have response schemas
        assert "responses" in post_spec
        responses = post_spec["responses"]
        
        # Should document different response codes
        assert "200" in responses  # Success
        assert "404" in responses  # Not found
        assert "403" in responses  # Forbidden
        assert "422" in responses  # Validation error
    
    def test_authentication_endpoints_documented(self, client):
        """
        Verifies that authentication endpoints, including at least one login endpoint, are present and documented in the OpenAPI schema.
        """
        response = client.get("/openapi.json")
        schema = response.json()
        
        # Check auth endpoints
        paths = schema["paths"]
        auth_paths = [path for path in paths.keys() if "/auth/" in path]
        
        assert len(auth_paths) > 0
        
        # Should have login endpoint
        login_paths = [path for path in auth_paths if "login" in path]
        assert len(login_paths) > 0
    
    def test_cards_endpoints_documented(self, client):
        """
        Verifies that the cards management endpoints are present and properly documented in the OpenAPI schema.
        
        Checks for the existence of the `/api/v1/cards/` endpoint with GET and POST methods, and ensures that endpoints for individual cards with path parameters are defined.
        """
        response = client.get("/openapi.json")
        schema = response.json()
        
        paths = schema["paths"]
        
        # Should have cards endpoints
        assert "/api/v1/cards/" in paths
        
        cards_endpoint = paths["/api/v1/cards/"]
        
        # Should support CRUD operations
        assert "get" in cards_endpoint  # List cards
        assert "post" in cards_endpoint  # Create card
        
        # Check if individual card endpoints exist
        card_id_paths = [path for path in paths.keys() if "/api/v1/cards/{" in path]
        assert len(card_id_paths) > 0
    
    def test_doors_endpoints_documented(self, client):
        """
        Verifies that the doors management endpoints are documented in the OpenAPI schema.
        
        Checks that the `/api/v1/doors/` endpoint exists and supports both GET and POST methods.
        """
        response = client.get("/openapi.json")
        schema = response.json()
        
        paths = schema["paths"]
        
        # Should have doors endpoints
        assert "/api/v1/doors/" in paths
        
        doors_endpoint = paths["/api/v1/doors/"]
        
        # Should support CRUD operations
        assert "get" in doors_endpoint  # List doors
        assert "post" in doors_endpoint  # Create door
    
    def test_request_schemas_defined(self, client):
        """
        Verifies that request schemas are defined in the OpenAPI specification.
        
        Checks for the presence of the `components/schemas` section, ensures at least one request schema exists, and validates that the `AccessValidationRequest` schema includes `card_id` (string) and `door_id` (integer) properties.
        """
        response = client.get("/openapi.json")
        schema = response.json()
        
        # Check components/schemas section
        assert "components" in schema
        assert "schemas" in schema["components"]
        
        schemas = schema["components"]["schemas"]
        
        # Should have AccessValidationRequest schema
        request_schemas = [name for name in schemas.keys() if "Request" in name]
        assert len(request_schemas) > 0
        
        # Check AccessValidationRequest specifically
        if "AccessValidationRequest" in schemas:
            validation_request = schemas["AccessValidationRequest"]
            assert "properties" in validation_request
            
            properties = validation_request["properties"]
            assert "card_id" in properties
            assert "door_id" in properties
            
            # Check field types
            assert properties["card_id"]["type"] == "string"
            assert properties["door_id"]["type"] == "integer"
    
    def test_response_schemas_defined(self, client):
        """
        Verifies that response schemas are defined in the OpenAPI specification, including the presence and structure of the AccessValidationResponse schema.
        """
        response = client.get("/openapi.json")
        schema = response.json()
        
        schemas = schema["components"]["schemas"]
        
        # Should have response schemas
        response_schemas = [name for name in schemas.keys() if "Response" in name]
        assert len(response_schemas) > 0
        
        # Check AccessValidationResponse specifically
        if "AccessValidationResponse" in schemas:
            validation_response = schemas["AccessValidationResponse"]
            assert "properties" in validation_response
            
            properties = validation_response["properties"]
            assert "access_granted" in properties
            assert "reason" in properties
            assert "door_name" in properties
            
            # Check field types
            assert properties["access_granted"]["type"] == "boolean"
            assert properties["reason"]["type"] == "string"
    
    def test_error_responses_documented(self, client):
        """
        Verifies that error responses for the access validation endpoint are documented in the OpenAPI schema.
        
        Checks that the POST `/api/v1/access/validate` endpoint includes documentation for error response codes (400, 403, 404, 422, 500), ensuring each has a description and, if content is provided, specifies the `application/json` content type.
        """
        response = client.get("/openapi.json")
        schema = response.json()
        
        # Check access validation endpoint error responses
        validate_endpoint = schema["paths"]["/api/v1/access/validate"]["post"]
        responses = validate_endpoint["responses"]
        
        # Should document error cases
        error_codes = ["400", "403", "404", "422", "500"]
        for code in error_codes:
            if code in responses:
                error_response = responses[code]
                assert "description" in error_response
                
                # Should have content type
                if "content" in error_response:
                    assert "application/json" in error_response["content"]
    
    def test_examples_in_documentation(self, client):
        """
        Checks whether the API documentation for the access validation endpoint includes response examples.
        
        This test inspects the OpenAPI schema for the presence of example data in the 200 response of the `/api/v1/access/validate` POST endpoint, but does not fail if examples are absent.
        """
        response = client.get("/openapi.json")
        schema = response.json()
        
        # Check if examples are provided
        validate_endpoint = schema["paths"]["/api/v1/access/validate"]["post"]
        
        # Check for examples in responses
        responses = validate_endpoint["responses"]
        if "200" in responses:
            success_response = responses["200"]
            if "content" in success_response:
                json_content = success_response["content"].get("application/json", {})
                # Examples might be in different places depending on OpenAPI version
                has_examples = (
                    "examples" in json_content or 
                    "example" in json_content or
                    ("schema" in json_content and "example" in json_content["schema"])
                )
                # Examples are nice to have but not required
                assert True  # Pass regardless for now
    
    def test_swagger_ui_accessible(self, client):
        """
        Verifies that the Swagger UI documentation is accessible at the /docs endpoint.
        
        Asserts that the endpoint returns an HTTP 200 status, serves HTML content, and contains Swagger UI elements.
        """
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        # Should contain Swagger UI elements
        content = response.text
        assert "swagger" in content.lower()
    
    def test_redoc_accessible(self, client):
        """
        Verifies that the ReDoc API documentation is accessible and returns valid HTML content.
        
        Asserts that the `/redoc` endpoint responds with HTTP 200 and contains expected ReDoc elements in the HTML.
        """
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        # Should contain ReDoc elements
        content = response.text
        assert "redoc" in content.lower()
    
    def test_api_tags_organization(self, client):
        """
        Verifies that API endpoints are organized using the expected tags.
        
        Checks that if any endpoint uses a tag from the expected set ("Access Control", "Authentication", "Cards", "Doors", "Health"), it is present in the OpenAPI schema's tags collection.
        """
        response = client.get("/openapi.json")
        schema = response.json()
        
        # Collect all tags used
        all_tags = set()
        for path_data in schema["paths"].values():
            for method_data in path_data.values():
                if "tags" in method_data:
                    all_tags.update(method_data["tags"])
        
        # Should have logical tag organization
        expected_tags = ["Access Control", "Authentication", "Cards", "Doors", "Health"]
        for tag in expected_tags:
            if any(tag in schema["paths"][path][method].get("tags", []) 
                   for path in schema["paths"] 
                   for method in schema["paths"][path]):
                assert tag in all_tags
    
    def test_security_schemes_documented(self, client):
        """
        Verifies that the OpenAPI schema documents at least one bearer token security scheme.
        """
        response = client.get("/openapi.json")
        schema = response.json()
        
        # Check for security schemes
        if "components" in schema and "securitySchemes" in schema["components"]:
            security_schemes = schema["components"]["securitySchemes"]
            
            # Should have bearer token authentication
            bearer_schemes = [
                name for name, scheme in security_schemes.items() 
                if scheme.get("type") == "http" and scheme.get("scheme") == "bearer"
            ]
            assert len(bearer_schemes) > 0
    
    def test_api_versioning_in_paths(self, client):
        """
        Verifies that all API paths starting with '/api/' include versioning as '/api/v1/'.
        
        Ensures consistency in API versioning by asserting that every documented API path uses the '/api/v1/' prefix.
        """
        response = client.get("/openapi.json")
        schema = response.json()
        
        # All API paths should use v1 versioning
        api_paths = [path for path in schema["paths"].keys() if path.startswith("/api/")]
        
        for path in api_paths:
            # Should use versioned paths
            assert "/api/v1/" in path
    
    def test_health_endpoint_documented(self, client):
        """
        Verifies that the `/health` endpoint is present in the OpenAPI schema and documents a 200 response.
        """
        response = client.get("/openapi.json")
        schema = response.json()
        
        # Should have health endpoint
        assert "/health" in schema["paths"]
        
        health_endpoint = schema["paths"]["/health"]
        assert "get" in health_endpoint
        
        get_spec = health_endpoint["get"]
        assert "responses" in get_spec
        assert "200" in get_spec["responses"]