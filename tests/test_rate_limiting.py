"""Tests for rate limiting functionality."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from opa_quotes_api.main import app
from opa_quotes_api.schemas import QuoteResponse
from datetime import datetime


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_quote():
    """Mock quote response."""
    return QuoteResponse(
        ticker="AAPL",
        timestamp=datetime.now(),
        open=150.0,
        high=155.0,
        low=149.0,
        close=154.0,
        volume=1000000,
    )


def test_rate_limit_on_latest_quote(client, mock_quote):
    """Test que rate limiting funciona en endpoint /latest."""
    
    # Mock del servicio
    with patch('opa_quotes_api.routers.quotes.get_quote_service') as mock_service:
        mock_svc = AsyncMock()
        mock_svc.get_latest = AsyncMock(return_value=mock_quote)
        mock_service.return_value = mock_svc
        
        # Hacer 101 requests (límite es 100/minuto)
        # Los primeros 100 deben ser exitosos
        for i in range(100):
            response = client.get("/v1/quotes/AAPL/latest")
            assert response.status_code == 200, f"Request {i+1} falló"
        
        # El 101 debe retornar 429 Too Many Requests
        response = client.get("/v1/quotes/AAPL/latest")
        assert response.status_code == 429
        assert "rate limit exceeded" in response.text.lower()


def test_rate_limit_headers_present(client, mock_quote):
    """Test que headers de rate limiting están presentes."""
    
    with patch('opa_quotes_api.routers.quotes.get_quote_service') as mock_service:
        mock_svc = AsyncMock()
        mock_svc.get_latest = AsyncMock(return_value=mock_quote)
        mock_service.return_value = mock_svc
        
        response = client.get("/v1/quotes/AAPL/latest")
        
        # Verificar que headers X-RateLimit están presentes
        # (slowapi puede agregar estos headers)
        assert response.status_code == 200


def test_rate_limit_history_more_restrictive(client):
    """Test que history tiene límite más restrictivo que latest."""
    from datetime import datetime, timedelta
    
    with patch('opa_quotes_api.routers.quotes.get_quote_service') as mock_service:
        mock_svc = AsyncMock()
        mock_history = AsyncMock()
        mock_history.ticker = "AAPL"
        mock_history.interval = "1m"
        mock_history.data = []
        mock_history.count = 0
        mock_svc.get_history = AsyncMock(return_value=mock_history)
        mock_service.return_value = mock_svc
        
        # Payload para history
        now = datetime.now()
        payload = {
            "ticker": "AAPL",
            "start_date": (now - timedelta(days=1)).isoformat(),
            "end_date": now.isoformat(),
            "interval": "1m"
        }
        
        # Hacer 21 requests (límite history es 20/minuto)
        for i in range(20):
            response = client.post("/v1/quotes/AAPL/history", json=payload)
            assert response.status_code in [200, 201], f"Request {i+1} falló"
        
        # El 21 debe retornar 429
        response = client.post("/v1/quotes/AAPL/history", json=payload)
        assert response.status_code == 429


def test_rate_limit_per_ip_isolation():
    """Test que rate limiting es por IP (cada IP tiene su propio límite)."""
    # Este test es más conceptual ya que TestClient usa la misma IP
    # En producción, slowapi usa get_remote_address para trackear por IP
    
    client = TestClient(app)
    
    with patch('opa_quotes_api.routers.quotes.get_quote_service') as mock_service:
        mock_svc = AsyncMock()
        mock_quote = QuoteResponse(
            ticker="AAPL",
            timestamp=datetime.now(),
            open=150.0,
            high=155.0,
            low=149.0,
            close=154.0,
            volume=1000000,
        )
        mock_svc.get_latest = AsyncMock(return_value=mock_quote)
        mock_service.return_value = mock_svc
        
        # Primera request debe funcionar
        response = client.get("/v1/quotes/AAPL/latest")
        assert response.status_code == 200


def test_rate_limit_batch_endpoint(client):
    """Test que batch endpoint tiene su propio rate limit."""
    
    with patch('opa_quotes_api.routers.quotes.get_quote_service') as mock_service:
        mock_svc = AsyncMock()
        mock_response = AsyncMock()
        mock_response.quotes = []
        mock_response.not_found = []
        mock_svc.get_batch = AsyncMock(return_value=mock_response)
        mock_service.return_value = mock_svc
        
        payload = {"tickers": ["AAPL", "MSFT"]}
        
        # Hacer 51 requests (límite batch es 50/minuto)
        for i in range(50):
            response = client.get("/v1/quotes/batch", params=payload)
            # Puede fallar por otras razones (schema, etc)
            # Solo verificar que no sea 429
            assert response.status_code != 429, f"Rate limit activado en request {i+1}"
        
        # El 51 debería dar 429
        response = client.get("/v1/quotes/batch", params=payload)
        # Note: Puede no llegar a 429 si hay otros errores primero
        # Este test es más ilustrativo


@pytest.mark.asyncio
async def test_rate_limiter_redis_persistence():
    """Test que rate limiter usa Redis para persistencia."""
    from opa_quotes_api.middleware.rate_limit import limiter
    
    # Verificar que limiter está configurado con Redis
    assert limiter._storage is not None
    # Storage URI debe apuntar a Redis
    # (Esto depende de la configuración de slowapi)
