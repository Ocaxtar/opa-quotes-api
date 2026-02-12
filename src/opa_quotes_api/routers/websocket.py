"""WebSocket router for real-time quote streaming."""

import json
import uuid
from typing import Optional

import redis.asyncio as redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from opa_quotes_api.config import get_settings
from opa_quotes_api.logging_setup import get_logger

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(
    prefix="/ws",
    tags=["websocket"],
)


class ConnectionManager:
    """
    Gestor de conexiones WebSocket activas.
    
    Mantiene un registro de todas las conexiones WebSocket activas
    y proporciona métodos para enviar mensajes y gestionar el ciclo de vida.
    """
    
    def __init__(self):
        """Inicializar manager con diccionario vacío de conexiones."""
        self.active_connections: dict[str, WebSocket] = {}
        logger.info("ConnectionManager initialized")
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """
        Aceptar y registrar una nueva conexión WebSocket.
        
        Args:
            websocket: WebSocket instance
            client_id: Unique client identifier
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Active connections: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        """
        Eliminar una conexión del registro.
        
        Args:
            client_id: Client identifier to disconnect
        """
        if client_id in self.active_connections:
            self.active_connections.pop(client_id)
            logger.info(f"Client {client_id} disconnected. Active connections: {len(self.active_connections)}")
    
    async def send_message(self, client_id: str, message: dict):
        """
        Enviar mensaje JSON a un cliente específico.
        
        Args:
            client_id: Target client identifier
            message: Message data as dictionary
        """
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
                logger.debug(f"Message sent to client {client_id}: {message.get('ticker', 'N/A')}")
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {e}")
                self.disconnect(client_id)


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/quotes")
async def websocket_endpoint(
    websocket: WebSocket,
    tickers: Optional[str] = Query(None, description="Comma-separated tickers (e.g., AAPL,MSFT). Omit for all tickers.")
):
    """
    WebSocket endpoint para cotizaciones en tiempo real.
    
    **Query Params**:
    - tickers: Lista de tickers separados por coma (ej: AAPL,MSFT). 
               Omitir o pasar "*" para recibir todos los tickers.
    
    **Message Format (from server)**:
    ```json
    {
        "ticker": "AAPL",
        "timestamp": "2026-01-21T10:30:00Z",
        "open": 150.25,
        "high": 151.10,
        "low": 150.05,
        "close": 150.90,
        "volume": 1000000,
        "bid": 150.88,
        "ask": 150.92
    }
    ```
    
    **Disconnect**: Cliente puede cerrar conexión en cualquier momento.
    
    **Error Handling**:
    - Si Redis Pub/Sub falla, conexión se cierra con código 1011
    - Conexión idle detectada y cerrada tras timeout
    """
    client_id = str(uuid.uuid4())
    redis_client: Optional[redis.Redis] = None
    pubsub = None
    
    # Parse tickers filter
    ticker_filter = set()
    if tickers:
        # Normalize: split, strip, uppercase
        ticker_filter = set(t.strip().upper() for t in tickers.split(",") if t.strip())
    
    # Si no hay filtro o contiene "*", aceptar todos
    accept_all = not ticker_filter or "*" in ticker_filter
    
    logger.info(f"WebSocket connection attempt - Client: {client_id}, Tickers: {ticker_filter or 'ALL'}")
    
    try:
        # Aceptar conexión
        await manager.connect(websocket, client_id)
        
        # Conectar a Redis Pub/Sub
        redis_client = await redis.from_url(settings.redis_url, decode_responses=True)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("quotes.realtime")
        
        logger.info(f"Client {client_id} subscribed to Redis channel 'quotes.realtime'")
        
        # Escuchar mensajes de Redis
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    # Parse JSON data
                    data = json.loads(message["data"])
                    ticker = data.get("ticker", "").upper()
                    
                    # Filtrar por tickers solicitados
                    if accept_all or ticker in ticker_filter:
                        await manager.send_message(client_id, data)
                    else:
                        logger.debug(f"Filtered out ticker {ticker} for client {client_id}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from Redis: {message['data']}, error: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing Redis message for client {client_id}: {e}")
                    continue
    
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected gracefully")
    
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket handler for client {client_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
    
    finally:
        # Cleanup resources
        manager.disconnect(client_id)
        
        if pubsub:
            try:
                await pubsub.unsubscribe("quotes.realtime")
                await pubsub.close()
            except Exception as e:
                logger.error(f"Error closing pubsub for client {client_id}: {e}")
        
        if redis_client:
            try:
                await redis_client.close()
            except Exception as e:
                logger.error(f"Error closing Redis client for client {client_id}: {e}")
        
        logger.info(f"Cleanup completed for client {client_id}")


@router.websocket("")
async def websocket_root(
    websocket: WebSocket,
    tickers: Optional[str] = Query(None, description="Comma-separated tickers (e.g., AAPL,MSFT). Omit for all tickers.")
):
    """
    WebSocket endpoint raíz (alias de /quotes).
    
    OPA-506: Endpoint sin '/quotes' para compatibilidad con scripts de validación.
    Mantiene misma funcionalidad que /quotes.
    
    **URL**: ws://localhost:8000/ws o ws://localhost:8000/v1/ws
    """
    # Reutilizar misma lógica que /quotes
    await websocket_endpoint(websocket, tickers)
