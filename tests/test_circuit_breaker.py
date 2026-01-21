"""Tests for circuit breaker functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pybreaker import CircuitBreaker
from opa_quotes_api.middleware.circuit_breaker import CircuitBreakerError


@pytest.fixture
def test_redis_breaker():
    """Create a test circuit breaker for Redis."""
    return CircuitBreaker(fail_max=3, reset_timeout=1, name="test_redis")


@pytest.fixture
def test_db_breaker():
    """Create a test circuit breaker for DB."""
    return CircuitBreaker(fail_max=2, reset_timeout=1, name="test_db")


@pytest.mark.asyncio
async def test_redis_breaker_opens_after_failures(test_redis_breaker):
    """Test que circuit breaker se abre tras múltiples fallos."""
    
    async def failing_operation():
        raise Exception("Redis connection failed")
    
    # Intentar 3 veces (fail_max configurado)
    for _ in range(3):
        with pytest.raises(Exception):
            await test_redis_breaker.call_async(failing_operation)
    
    # El cuarto intento debe levantar CircuitBreakerError
    with pytest.raises(CircuitBreakerError):
        await test_redis_breaker.call_async(failing_operation)


@pytest.mark.asyncio
async def test_circuit_breaker_allows_success(test_redis_breaker):
    """Test que circuit breaker permite operaciones exitosas."""
    
    async def successful_operation():
        return "success"
    
    result = await test_redis_breaker.call_async(successful_operation)
    assert result == "success"


@pytest.mark.asyncio
async def test_circuit_breaker_metrics_updated():
    """Test que métricas Prometheus están configuradas."""
    from opa_quotes_api.middleware.circuit_breaker import circuit_state
    
    # Verificar que métricas están inicializadas
    metric_family = circuit_state.collect()[0]
    redis_metric = next(
        (m for m in metric_family.samples if m.labels.get('service') == 'redis'),
        None
    )
    
    assert redis_metric is not None
    # Inicialmente debe estar cerrado (0)
    assert redis_metric.value == 0


@pytest.mark.asyncio
async def test_cache_service_with_working_redis():
    """Test que CacheService funciona correctamente con Redis operativo."""
    from opa_quotes_api.services.cache_service import CacheService
    
    # Mock Redis client con respuestas exitosas
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.setex = AsyncMock()
    
    cache_service = CacheService(mock_redis)
    
    # Test get (cache miss)
    result = await cache_service.get("test_key")
    assert result is None
    
    # Test set
    success = await cache_service.set("test_key", "test_value")
    assert success is True


@pytest.mark.asyncio
async def test_quote_service_fallback_on_cache_failure():
    """Test que QuoteService hace fallback cuando cache falla."""
    from opa_quotes_api.services.quote_service import QuoteService
    from opa_quotes_api.services.cache_service import CacheService
    from opa_quotes_api.repository.quote_repository import QuoteRepository
    from opa_quotes_api.schemas import QuoteResponse
    from datetime import datetime, timezone
    
    # Mock Redis que lanza error (simular circuit open)
    mock_redis = AsyncMock()
    mock_cache = CacheService(mock_redis)
    
    # Mock para que cache.get lance CircuitBreakerError
    async def mock_get_error(key):
        raise CircuitBreakerError("test_breaker")
    
    mock_cache.get = mock_get_error
    
    # Configure repository to return a quote
    mock_repository = AsyncMock(spec=QuoteRepository)
    mock_quote = QuoteResponse(
        ticker="AAPL",
        timestamp=datetime.now(timezone.utc),
        open=150.0,
        high=155.0,
        low=149.0,
        close=154.0,
        volume=1000000,
    )
    mock_repository.get_latest = AsyncMock(return_value=mock_quote)
    
    service = QuoteService(cache=mock_cache, repository=mock_repository)
    
    # Debe hacer fallback a BD y devolver el quote
    result = await service.get_latest("AAPL")
    
    assert result is not None
    assert result.ticker == "AAPL"
    mock_repository.get_latest.assert_called_once()


@pytest.mark.asyncio
async def test_circuit_breaker_configuration():
    """Test que circuit breakers están configurados correctamente."""
    from opa_quotes_api.middleware.circuit_breaker import redis_breaker, db_breaker
    from opa_quotes_api.config import get_settings
    
    settings = get_settings()
    
    # Verificar nombres
    assert redis_breaker.name == "redis"
    assert db_breaker.name == "timescaledb"
    
    # Verificar que tienen listeners configurados
    assert len(redis_breaker._listeners) > 0
    assert len(db_breaker._listeners) > 0
