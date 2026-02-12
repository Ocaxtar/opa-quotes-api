# WebSocket API - Real-Time Quotes

## Overview

Este documento describe el contrato completo de la API WebSocket para streaming de cotizaciones en tiempo real.

**Relacionado con**: OPA-506, OPA-482

---

## Endpoints Disponibles

| Endpoint | Descripción | Recomendado |
|----------|-------------|-------------|
| `ws://localhost:8000/ws/quotes` | Endpoint con path explícito (sin versión) | ✅ Scripts validación |
| `ws://localhost:8000/ws` | Endpoint raíz (sin versión) | ✅ Compatibilidad legacy |
| `ws://localhost:8000/v1/ws/quotes` | Endpoint versionado con path | ✅ Integraciones API |
| `ws://localhost:8000/v1/ws` | Endpoint versionado raíz | ✅ Integraciones API |

**Notas**:
- Todos los endpoints son funcionalmente idénticos
- Se recomienda usar versión explícita (`/v1/ws/quotes`) para nuevas integraciones
- Endpoints sin versión (`/ws`) mantenidos para compatibilidad con scripts de validación

---

## Query Parameters

### `tickers` (opcional)

Lista de tickers separados por coma para filtrar cotizaciones.

**Formato**: `?tickers=TICKER1,TICKER2,TICKER3`

**Comportamiento**:
- **Omitido**: Recibe cotizaciones de **todos** los tickers disponibles
- **`*`**: Recibe cotizaciones de **todos** los tickers (alias explícito)
- **Lista específica**: Recibe solo los tickers listados (case-insensitive)

**Ejemplos**:
```
ws://localhost:8000/ws/quotes?tickers=AAPL,MSFT,GOOGL
ws://localhost:8000/ws/quotes?tickers=*
ws://localhost:8000/ws/quotes  (sin parámetro = todos)
```

---

## Message Format

### Servidor → Cliente

```json
{
  "ticker": "AAPL",
  "timestamp": "2026-02-12T10:30:00.123456Z",
  "open": 150.25,
  "high": 151.10,
  "low": 150.05,
  "close": 150.90,
  "volume": 1000000,
  "bid": 150.88,
  "ask": 150.92
}
```

**Campos**:
- `ticker` (string): Símbolo del ticker (uppercase)
- `timestamp` (string): Timestamp ISO 8601 con microsegundos (UTC)
- `open` (float): Precio de apertura
- `high` (float): Precio máximo
- `low` (float): Precio mínimo
- `close` (float): Precio actual/cierre
- `volume` (int): Volumen acumulado
- `bid` (float): Precio de compra (opcional)
- `ask` (float): Precio de venta (opcional)

**Frecuencia**: Continuo (stream en tiempo real según disponibilidad de datos)

**Orden**: No garantizado por ticker (los mensajes llegan según publicación en Redis)

---

## Connection Lifecycle

### 1. Handshake

**Request**:
```http
GET /ws/quotes?tickers=AAPL,MSFT HTTP/1.1
Host: localhost:8000
Upgrade: websocket
Connection: Upgrade
```

**Response (Success - 101)**:
```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
```

**Response (Error - 403)**:
- Causa: CORS policy violación (bloqueado en pre-flight)
- Solución: Verificar origen permitido en `cors_origins` config

**Response (Error - 503)**:
- Causa: Servicio Redis Pub/Sub no disponible
- Solución: Verificar que `opa-quotes-streamer` esté publicando en `quotes.realtime`

### 2. Data Streaming

Una vez conectado, el servidor envía mensajes JSON de forma continua sin necesidad de solicitud del cliente.

**No se requiere**:
- ❌ Enviar mensajes de "keep-alive" desde cliente
- ❌ Confirmar recepción de mensajes (ACK)
- ❌ Re-suscribir a tickers

**Comportamiento**:
- Mensajes enviados inmediatamente cuando Redis publica en canal `quotes.realtime`
- Filtrado por `tickers` se aplica en servidor (no se envían tickers no solicitados)

### 3. Disconnection

**Cliente → Servidor (Graceful)**:
```javascript
websocket.close(1000, "Client closing");
```

**Servidor → Cliente (Error)**:
```javascript
// Código 1011: Internal Server Error (Redis fallo)
websocket.close(1011, "Internal server error");
```

**Cleanup automático**:
- Redis Pub/Sub unsubscribe
- Conexión eliminada del manager
- Recursos liberados

---

## Ejemplos de Uso

### Python (websockets)

```python
import asyncio
import websockets
import json

async def stream_quotes():
    uri = "ws://localhost:8000/ws/quotes?tickers=AAPL,MSFT"
    
    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri}")
        
        async for message in websocket:
            data = json.loads(message)
            print(f"{data['ticker']}: ${data['close']} @ {data['timestamp']}")

asyncio.run(stream_quotes())
```

### JavaScript (Browser)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/quotes?tickers=AAPL,MSFT');

ws.onopen = () => {
    console.log('WebSocket connected');
};

ws.onmessage = (event) => {
    const quote = JSON.parse(event.data);
    console.log(`${quote.ticker}: $${quote.close} @ ${quote.timestamp}`);
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

ws.onclose = (event) => {
    console.log(`WebSocket closed: ${event.code} ${event.reason}`);
};
```

### cURL (Testing)

```bash
# Nota: cURL no soporta WebSocket nativamente, usar websocat
websocat ws://localhost:8000/ws/quotes?tickers=AAPL
```

---

## Error Handling

### Cliente

**Best Practices**:
1. **Timeout de conexión**: 30 segundos para handshake
2. **Reconnect automático**: Exponential backoff (1s, 2s, 4s, 8s, max 60s)
3. **Validación de mensajes**: Verificar estructura JSON antes de procesar
4. **Buffer overflow**: Limitar mensajes en memoria (ej: 1000 últimos)

**Ejemplo de reconnect**:
```python
import asyncio

async def connect_with_retry(uri, max_retries=5):
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            async with websockets.connect(uri) as ws:
                # Conexión exitosa, resetear delay
                retry_delay = 1
                
                async for message in ws:
                    yield message
                    
        except Exception as e:
            print(f"Error: {e}. Retrying in {retry_delay}s...")
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)  # Max 60s
```

### Servidor

**Códigos de cierre**:
- `1000`: Normal closure (cliente desconectó)
- `1011`: Internal server error (Redis Pub/Sub fallo)

**Logging**:
- Cada conexión/desconexión registrada con `client_id`
- Errores de parsing JSON registrados pero no cierran conexión
- Errores de envío cierran conexión automáticamente

---

## Performance Considerations

### Cliente

**Recomendaciones para 300 tickers**:
1. **Usar librerías asíncronas** (asyncio, aiohttp) en Python
2. **Procesar mensajes en batch** (ej: acumular 100ms antes de actualizar UI)
3. **Implementar backpressure** (pausar si buffer > 10,000 mensajes)
4. **Monitorear latencia** (timestamp servidor vs timestamp recepción)

### Servidor

**Capacidad actual** (por instancia de API):
- **Conexiones simultáneas**: 1,000+ clientes
- **Throughput**: 10,000 mensajes/seg (con Redis local)
- **Latencia p99**: < 50ms (publicación Redis → envío a cliente)

**Limitaciones conocidas**:
- Redis Pub/Sub no garantiza orden global entre múltiples publishers
- Reconnect no recibe mensajes perdidos durante desconexión (stateless)

---

## Testing & Validation

### Health Check

Antes de conectar WebSocket, verificar API:
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"0.1.0","repository":"opa-quotes-api"}
```

### WebSocket Connectivity

Script de validación básica:
```python
# scripts/validation/test_websocket_health.py

import asyncio
import websockets

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri, timeout=10) as ws:
            print("✓ WebSocket handshake successful")
            
            # Esperar primer mensaje
            message = await asyncio.wait_for(ws.recv(), timeout=30)
            print(f"✓ Received first message: {message[:100]}...")
            
            return True
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"✗ Handshake failed: {e.status_code} {e.headers}")
        return False
    except asyncio.TimeoutError:
        print("✗ Timeout waiting for data")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_websocket())
    exit(0 if success else 1)
```

### Load Testing

Para validar 300 tickers (OPA-482):
```bash
python scripts/benchmark/ws_latency_benchmark.py \
  --ws-url ws://localhost:8000/ws/quotes \
  --ticker-count 300 \
  --duration 300  # 5 minutos
```

---

## Troubleshooting

### 403 Forbidden en Handshake

**Síntoma**: `websockets.exceptions.InvalidStatusCode: server rejected WebSocket connection: HTTP 403`

**Causas posibles**:
1. **CORS policy**: Origen no permitido en `cors_origins` config
   - **Solución**: Verificar `effective_cors_origins` en logs de startup
   - **Dev**: Debe ser `["*"]` (permitir todos)

2. **Middleware bloqueando**: Custom middleware interceptando request
   - **Solución**: Revisar logs para mensajes de middleware

3. **Proxy inverso**: Nginx/Traefik no configurado para WebSocket
   - **Solución**: Agregar headers `Upgrade: websocket` y `Connection: Upgrade`

### No Recibo Mensajes

**Síntoma**: Conexión exitosa pero sin datos streaming

**Causas posibles**:
1. **Redis Pub/Sub no publicando**: `opa-quotes-streamer` no está corriendo
   - **Solución**: Verificar `docker ps | grep streamer`
   - **Verificar canal**: `redis-cli SUBSCRIBE quotes.realtime`

2. **Filtro de tickers demasiado restrictivo**: Ningún ticker coincide
   - **Solución**: Probar sin query param (todos los tickers)

3. **Redis connection failed**: Servidor no puede conectar a Redis
   - **Solución**: Revisar logs de API para errores de Redis

### High Latency (> 1s)

**Síntoma**: Mensajes llegan con delay significativo

**Causas posibles**:
1. **Red congestion**: Problemas de red entre cliente y servidor
   - **Solución**: Medir latencia con `ping` y `traceroute`

2. **Backpressure en servidor**: Demasiados clientes conectados
   - **Solución**: Verificar métricas Prometheus en `/metrics`

3. **Processing bottleneck en cliente**: Cliente no procesa mensajes rápido
   - **Solución**: Implementar async processing, evitar sync I/O

---

## Changelog

| Fecha | Issue | Cambio |
|-------|-------|--------|
| 2026-02-12 | OPA-506 | Agregados endpoints `/ws` y `/ws/quotes` sin versión |
| 2026-02-12 | OPA-506 | Documentado contrato completo WebSocket |

---

**Documento creado**: 2026-02-12  
**Última actualización**: 2026-02-12  
**Versión API**: 0.1.0  
**Mantenedor**: OPA Team
