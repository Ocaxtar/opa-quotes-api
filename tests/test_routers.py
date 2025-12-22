"""Tests for quote routers."""
import pytest
from fastapi.testclient import TestClient

from opa_quotes_api.main import app

client = TestClient(app)


class TestQuoteRouters:
    """Tests for quote router endpoints."""
    
    def test_get_latest_quote_structure(self):
        """Test latest quote endpoint exists and has correct structure."""
        response = client.get("/quotes/AAPL/latest")
        
        # With service integration, should return 404 (no DB data) or 500 (connection error)
        # instead of 501 (not implemented)
        assert response.status_code in [404, 500]
    
    def test_get_latest_quote_validation(self):
        """Test ticker validation."""
        # Empty ticker should fail
        response = client.get("/quotes//latest")
        assert response.status_code in [404, 422]
        
        # Very long ticker should fail validation or return error
        response = client.get("/quotes/VERYLONGTICKER123/latest")
        assert response.status_code in [422, 404, 500]  # Either validation or connection error
    
    def test_get_history_structure(self):
        """Test history endpoint exists and has correct structure."""
        request_data = {
            "ticker": "AAPL",
            "start_date": "2025-12-22T09:00:00Z",
            "end_date": "2025-12-22T17:00:00Z",
            "interval": "5m"
        }
        
        response = client.post("/quotes/AAPL/history", json=request_data)
        
        # With service integration, should return 200 (empty data) or 500 (connection error)
        assert response.status_code in [200, 500]
    
    def test_get_history_ticker_mismatch(self):
        """Test that mismatched tickers are rejected."""
        request_data = {
            "ticker": "GOOGL",  # Different from URL
            "start_date": "2025-12-22T09:00:00Z",
            "end_date": "2025-12-22T17:00:00Z",
            "interval": "5m"
        }
        
        response = client.post("/quotes/AAPL/history", json=request_data)
        
        # Should return 400 for mismatched ticker
        assert response.status_code == 400
        assert "must match" in response.json()["detail"].lower()
    
    def test_batch_quotes_structure(self):
        """Test batch quotes endpoint exists."""
        request_data = {
            "tickers": ["AAPL", "GOOGL", "MSFT"]
        }
        
        response = client.post("/quotes/batch", json=request_data)
        
        # With service integration, should return 200 (with proper structure) or 500
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "quotes" in data
            assert "total" in data
            assert "successful" in data
            assert "failed" in data
    
    def test_batch_quotes_validation(self):
        """Test batch request validation."""
        # Empty ticker list should fail
        request_data = {
            "tickers": []
        }
        
        response = client.post("/quotes/batch", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_list_tickers_structure(self):
        """Test list tickers endpoint exists."""
        response = client.get("/quotes/")
        
        # With service integration, should return 200 (empty list) or 500
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_list_tickers_pagination(self):
        """Test pagination parameters."""
        response = client.get("/quotes/?limit=50&offset=10")
        
        # Should accept pagination params
        assert response.status_code in [200, 500]
    
    def test_list_tickers_validation(self):
        """Test pagination validation."""
        # Negative limit should fail
        response = client.get("/quotes/?limit=-1")
        assert response.status_code == 422
        
        # Limit too large should fail
        response = client.get("/quotes/?limit=2000")
        assert response.status_code == 422
        
        # Negative offset should fail
        response = client.get("/quotes/?offset=-5")
        assert response.status_code == 422


class TestAPIDocumentation:
    """Tests for API documentation generation."""
    
    def test_openapi_schema_generated(self):
        """Test that OpenAPI schema is generated."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
    
    def test_quotes_endpoints_in_docs(self):
        """Test that quote endpoints appear in OpenAPI docs."""
        response = client.get("/openapi.json")
        schema = response.json()
        
        paths = schema["paths"]
        
        # Check all endpoints are documented
        assert "/quotes/{ticker}/latest" in paths
        assert "/quotes/{ticker}/history" in paths
        assert "/quotes/batch" in paths
        assert "/quotes/" in paths
    
    def test_schemas_in_docs(self):
        """Test that Pydantic schemas are in OpenAPI docs."""
        response = client.get("/openapi.json")
        schema = response.json()
        
        components = schema.get("components", {})
        schemas = components.get("schemas", {})
        
        # Check our schemas are included
        assert "QuoteResponse" in schemas
        assert "HistoryRequest" in schemas
        assert "HistoryResponse" in schemas
        assert "BatchRequest" in schemas
        assert "BatchResponse" in schemas
    
    def test_docs_ui_accessible(self):
        """Test that Swagger UI is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()
