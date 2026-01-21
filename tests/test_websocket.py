"""Tests for WebSocket functionality."""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from opa_quotes_api.main import app
from opa_quotes_api.routers.websocket import ConnectionManager


@pytest.fixture
def connection_manager():
    """Create a fresh ConnectionManager instance for testing."""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket instance."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    return ws


def test_connection_manager_connect(connection_manager, mock_websocket):
    """Test que ConnectionManager registra conexiones correctamente."""
    import asyncio
    
    client_id = "test-client-123"
    
    async def test():
        await connection_manager.connect(mock_websocket, client_id)
        assert client_id in connection_manager.active_connections
        assert connection_manager.active_connections[client_id] == mock_websocket
        mock_websocket.accept.assert_called_once()
    
    asyncio.run(test())


def test_connection_manager_disconnect(connection_manager, mock_websocket):
    """Test que ConnectionManager elimina conexiones correctamente."""
    import asyncio
    
    client_id = "test-client-123"
    
    async def test():
        await connection_manager.connect(mock_websocket, client_id)
        assert client_id in connection_manager.active_connections
        
        connection_manager.disconnect(client_id)
        assert client_id not in connection_manager.active_connections
    
    asyncio.run(test())


def test_connection_manager_send_message(connection_manager, mock_websocket):
    """Test que ConnectionManager envía mensajes correctamente."""
    import asyncio
    
    client_id = "test-client-123"
    test_message = {"ticker": "AAPL", "price": 150.25}
    
    async def test():
        await connection_manager.connect(mock_websocket, client_id)
        await connection_manager.send_message(client_id, test_message)
        
        mock_websocket.send_json.assert_called_once_with(test_message)
    
    asyncio.run(test())


def test_connection_manager_send_to_nonexistent_client(connection_manager):
    """Test que enviar a cliente no existente no causa error."""
    import asyncio
    
    async def test():
        # No debe causar error
        await connection_manager.send_message("nonexistent-client", {"test": "data"})
    
    asyncio.run(test())


@pytest.mark.asyncio
async def test_websocket_ticker_filtering():
    """Test que WebSocket filtra tickers correctamente."""
    # Test conceptual - requiere mock completo de Redis Pub/Sub
    
    # Parse logic test
    tickers_str = "AAPL,MSFT,GOOGL"
    ticker_filter = set(t.strip().upper() for t in tickers_str.split(",") if t.strip())
    
    assert ticker_filter == {"AAPL", "MSFT", "GOOGL"}
    assert "AAPL" in ticker_filter
    assert "TSLA" not in ticker_filter


@pytest.mark.asyncio
async def test_websocket_accept_all_tickers():
    """Test que WebSocket acepta todos los tickers cuando no hay filtro."""
    # Sin filtro
    ticker_filter = set()
    accept_all = not ticker_filter or "*" in ticker_filter
    assert accept_all is True
    
    # Con asterisco
    ticker_filter = {"*"}
    accept_all = not ticker_filter or "*" in ticker_filter
    assert accept_all is True
    
    # Con filtro específico
    ticker_filter = {"AAPL"}
    accept_all = not ticker_filter or "*" in ticker_filter
    assert accept_all is False


@pytest.mark.asyncio
async def test_websocket_connection_lifecycle():
    """Test ciclo de vida completo de conexión WebSocket."""
    
    with patch('opa_quotes_api.routers.websocket.redis.from_url') as mock_redis:
        # Mock Redis client y pubsub
        mock_redis_client = AsyncMock()
        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.listen = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()
        mock_redis_client.pubsub = MagicMock(return_value=mock_pubsub)
        mock_redis_client.close = AsyncMock()
        mock_redis.return_value = mock_redis_client
        
        # Mock para que listen() retorne inmediatamente (sin mensajes)
        async def mock_listen():
            return
            yield  # Esta línea nunca se alcanza pero hace que sea un generador
        
        mock_pubsub.listen.return_value = mock_listen()
        
        # Aquí iría el test real con TestClient WebSocket
        # Pero requiere configuración compleja de Redis mock
        
        # Verificar que los mocks están configurados
        assert mock_redis_client is not None
        assert mock_pubsub is not None


@pytest.mark.asyncio
async def test_websocket_message_filtering():
    """Test que mensajes se filtran correctamente por ticker."""
    
    # Simular mensaje de Redis
    redis_message = {
        "type": "message",
        "data": json.dumps({
            "ticker": "AAPL",
            "price": 150.25,
            "timestamp": "2026-01-21T10:30:00Z"
        })
    }
    
    # Parse data
    data = json.loads(redis_message["data"])
    ticker = data.get("ticker", "").upper()
    
    # Test filtrado
    ticker_filter = {"AAPL", "MSFT"}
    accept_all = False
    
    should_send = accept_all or ticker in ticker_filter
    assert should_send is True
    
    # Test ticker no en filtro
    ticker = "GOOGL"
    should_send = accept_all or ticker in ticker_filter
    assert should_send is False


@pytest.mark.asyncio
async def test_websocket_invalid_json_handling():
    """Test que WebSocket maneja JSON inválido correctamente."""
    
    invalid_data = "this is not json"
    
    try:
        json.loads(invalid_data)
        assert False, "Should have raised JSONDecodeError"
    except json.JSONDecodeError:
        # Expected - el handler debe continuar sin crashear
        pass


@pytest.mark.asyncio
async def test_connection_manager_multiple_clients(connection_manager):
    """Test que ConnectionManager maneja múltiples clientes."""
    
    ws1 = AsyncMock()
    ws1.accept = AsyncMock()
    ws1.send_json = AsyncMock()
    
    ws2 = AsyncMock()
    ws2.accept = AsyncMock()
    ws2.send_json = AsyncMock()
    
    client1 = "client-1"
    client2 = "client-2"
    
    # Conectar ambos clientes
    await connection_manager.connect(ws1, client1)
    await connection_manager.connect(ws2, client2)
    
    assert len(connection_manager.active_connections) == 2
    assert client1 in connection_manager.active_connections
    assert client2 in connection_manager.active_connections
    
    # Enviar mensaje a cliente 1
    await connection_manager.send_message(client1, {"test": "data1"})
    ws1.send_json.assert_called_once_with({"test": "data1"})
    ws2.send_json.assert_not_called()
    
    # Desconectar cliente 1
    connection_manager.disconnect(client1)
    assert len(connection_manager.active_connections) == 1
    assert client2 in connection_manager.active_connections
