# opa-quotes-api

**FastAPI REST + WebSockets API para servir cotizaciones en tiempo real**

![CI](https://github.com/Ocaxtar/opa-quotes-api/workflows/CI/badge.svg)
![Security](https://github.com/Ocaxtar/opa-quotes-api/workflows/Security/badge.svg)
[![codecov](https://codecov.io/gh/Ocaxtar/opa-quotes-api/branch/main/graph/badge.svg)](https://codecov.io/gh/Ocaxtar/opa-quotes-api)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)

## 📋 Descripción

API REST y WebSockets para servir cotizaciones de mercado en tiempo real del ecosistema OPA_Machine. Consume datos de `opa-quotes-storage` (TimescaleDB) y los expone mediante endpoints REST y streams WebSocket.

**Repositorio**: `opa-quotes-api`  
**Módulo**: 5 (Cotización)  
**Tipo**: API Service  
**Fase**: 1 (Desarrollo Inicial)

## 🎯 Responsabilidades

1. **API REST**:
   - `GET /quotes/{ticker}/latest` → Última cotización
   - `GET /quotes/{ticker}/history` → Histórico con filtros (date range, interval)
   - `GET /quotes/batch` → Múltiples tickers en una consulta
   - Health check endpoint (`/health`)

2. **WebSocket Streaming**:
   - `WS /v1/ws/quotes?tickers={tickers}` → Stream en tiempo real
   - Filtrado por tickers (AAPL,MSFT o todos)
   - Integración con Redis Pub/Sub (canal `quotes.realtime`)
   - ConnectionManager para múltiples clientes concurrentes
   - Heartbeat para mantener conexión activa

3. **Performance**:
   - Caching Redis para last quote (TTL: 5s)
   - Rate limiting por cliente (100 req/min)
   - Response time <100ms (p95)

## 🏗️ Arquitectura

### Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Framework | FastAPI | 0.104+ |
| ORM | SQLAlchemy | 2.0+ |
| DB Driver | psycopg2-binary | 2.9+ |
| Cache | Redis | 7+ (via redis-py) |
| WebSockets | websockets | 12+ |
| Validation | Pydantic | 2.5+ |
| Monitoring | Prometheus | (client_python) |

### Dependencias Upstream

- **opa-quotes-storage** → TimescaleDB con hypertable `quotes.real_time`

### Dependencias Downstream

- **opa-capacity-compute** → Consume cotizaciones para análisis MIPL
- **opa-prediction-features** → Consume para feature engineering

## 🚀 Setup Local

### Prerrequisitos

- Python 3.12+
- Poetry 1.7+
- Docker & Docker Compose
- TimescaleDB operativo (vía opa-quotes-storage)
- Redis 7+

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/Ocaxtar/opa-quotes-api.git
cd opa-quotes-api

# Instalar dependencias
poetry install

# Configurar variables de entorno
cp .env.example .env
# Editar .env con credenciales si es necesario

# Levantar servicios locales (Redis + PostgreSQL/TimescaleDB)
docker-compose up -d

# Verificar que los servicios están operativos
docker-compose ps

# Ejecutar la aplicación
poetry run python -m opa_quotes_api.dev_server
```

La API estará disponible en:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

### Docker Compose

**Desarrollo local** (`docker-compose.yml`):
```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down

# Limpiar datos
docker-compose down -v
```

**Testing** (`docker-compose.test.yml`):
```bash
# Iniciar servicios de test (puertos diferentes)
docker-compose -f docker-compose.test.yml up -d

# Ejecutar tests
poetry run pytest

# Limpiar
docker-compose -f docker-compose.test.yml down -v
```

**Servicios incluidos**:
- **Redis**: Puerto 6379 (dev) / 6380 (test) - Cache de cotizaciones
- **PostgreSQL + TimescaleDB**: Puerto 5432 (dev) / 5433 (test) - Base de datos
- **API**: Puerto 8000 - FastAPI con hot reload

Ver [init-db/README.md](init-db/README.md) para más detalles sobre la configuración de Docker.
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
```

## 📡 Uso

### Endpoints REST

**Última cotización**:
```bash
curl http://localhost:8000/quotes/AAPL/latest
```

```json
{
  "ticker": "AAPL",
  "timestamp": "2025-12-22T10:30:00Z",
  "open": 150.25,
  "high": 151.10,
  "low": 150.05,
  "close": 150.90,
  "volume": 1250000,
  "bid": 150.88,
  "ask": 150.92
}
```

**Histórico (últimas 24h)**:
```bash
curl "http://localhost:8000/quotes/AAPL/history?hours=24&interval=5m"
```

**Batch (múltiples tickers)**:
```bash
curl -X POST http://localhost:8000/quotes/batch \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL", "MSFT", "GOOGL"]}'
```

### WebSocket Streaming

**Endpoint**: `ws://localhost:8000/v1/ws/quotes`

**Conexión con filtro de tickers**:
```bash
# Suscribirse a AAPL y MSFT solamente
ws://localhost:8000/v1/ws/quotes?tickers=AAPL,MSFT

# Suscribirse a todos los tickers (omitir parámetro)
ws://localhost:8000/v1/ws/quotes
```

**Cliente Python**:
```python
import asyncio
import websockets
import json

async def stream_quotes():
    uri = "ws://localhost:8000/v1/ws/quotes?tickers=AAPL,MSFT"
    
    async with websockets.connect(uri) as ws:
        print("✅ Conectado al WebSocket")
        
        try:
            async for message in ws:
                quote = json.loads(message)
                print(f"{quote['ticker']}: ${quote['close']:.2f} @ {quote['timestamp']}")
        except websockets.exceptions.ConnectionClosed:
            print("❌ Conexión cerrada")

asyncio.run(stream_quotes())
```

**Cliente JavaScript (Browser)**:
```javascript
const ws = new WebSocket('ws://localhost:8000/v1/ws/quotes?tickers=AAPL,MSFT');

ws.onopen = () => {
    console.log('✅ Conectado al WebSocket');
};

ws.onmessage = (event) => {
    const quote = JSON.parse(event.data);
    console.log(`${quote.ticker}: $${quote.close} @ ${quote.timestamp}`);
};

ws.onerror = (error) => {
    console.error('❌ Error:', error);
};

ws.onclose = () => {
    console.log('❌ Conexión cerrada');
};
```

**Formato de mensajes**:
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

**Cliente HTML interactivo**:

Incluido en `docs/examples/websocket-client.html`. Abrir en navegador:

```bash
# Desde raíz del proyecto
open docs/examples/websocket-client.html
# o
python -m http.server 8080
# Luego visitar http://localhost:8080/docs/examples/websocket-client.html
```

## 🧪 Testing

### Tests Unitarios

```bash
# Todos los tests
poetry run pytest

# Solo unitarios
poetry run pytest tests/unit/

# Con coverage
poetry run pytest --cov=opa_quotes_api --cov-report=html
```

### Tests de Integración

```bash
# Requiere TimescaleDB + Redis operativos
poetry run pytest tests/integration/
```

### Tests de Performance

```bash
# Benchmark de latencia
poetry run python tests/performance/latency_test.py

# Carga (100 req/s durante 60s)
poetry run locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

## 📊 Performance

### Targets

| Métrica | Target | Actual |
|---------|--------|--------|
| Latency (p95) | <100ms | TBD |
| Throughput | 1000 req/s | TBD |
| Cache hit rate | >90% | TBD |
| Uptime | 99.9% | TBD |

### Caching Strategy

- **Redis TTL**: 5 segundos para última cotización
- **Key pattern**: `quote:{ticker}:latest`
- **Invalidación**: On demand (cuando llega nueva cotización)

## 🔗 Integración con Ecosistema

### Contratos de API

Este servicio implementa los siguientes contratos formales:

#### POST /quotes/batch

**Contract**: [Quotes Batch Contract](https://github.com/Ocaxtar/opa-supervisor/blob/main/docs/contracts/apis/quotes-batch.md)

- **Role**: Consumer
- **Producer**: opa-quotes-streamer
- **Invariants**: INV-101 to INV-107 (API guarantees)
- **Validation**: Unit tests in `tests/test_quotes_batch.py`

**Contract invariants satisfied**:
- ✅ **INV-101**: Returns 201 if at least 1 quote persists
- ✅ **INV-102**: Returns 422 for invalid payload
- ✅ **INV-103**: Response includes `created` count (exact DB row count)
- ✅ **INV-104**: Commits transaction before returning response
- ✅ **INV-105**: Returns detailed errors array on partial failure

**Testing contract compliance**:
```bash
# Verify contract compliance
pytest tests/test_quotes_batch.py -v

# Manual verification
curl -X POST http://localhost:8000/quotes/batch \
  -H "Content-Type: application/json" \
  -d '{"quotes":[{"ticker":"AAPL","timestamp":"2026-01-12T10:00:00Z","close":175.23,"source":"yfinance"}]}'

# Expected response (201):
# {
#   "status": "success",
#   "created": 1,
#   "failed": 0
# }
```

**Common validation errors (422)**:
- Missing required fields (`ticker`, `timestamp`, `close`, `source`)
- Invalid ticker format (must match `^[A-Z]{1,5}$`)
- Invalid timestamp (must be ISO 8601 with timezone)
- Invalid source (must be `yfinance`, `fmp`, or `manual`)

#### Other Contracts

Ver: `OPA_Machine/docs/contracts/apis/quotes-api-contract.md`

**Endpoints estandarizados**:
- `/health` → Health check (TimescaleDB + Redis)
- `/metrics` → Prometheus metrics
- `/docs` → OpenAPI/Swagger UI

### Eventos

| Evento | Descripción | Payload |
|--------|-------------|---------|
| `quote.requested` | Cliente solicita cotización | `{ticker, endpoint, timestamp}` |
| `quote.served` | Cotización servida correctamente | `{ticker, latency_ms, from_cache}` |
| `quote.error` | Error al servir cotización | `{ticker, error_type, message}` |

## 🛠️ Desarrollo

### Estructura del Proyecto

```
opa-quotes-api/
├── src/
│   └── opa_quotes_api/
│       ├── __init__.py
│       ├── main.py              # FastAPI app
│       ├── routers/
│       │   ├── quotes.py        # REST endpoints
│       │   └── websocket.py     # WS endpoints
│       ├── services/
│       │   ├── quote_service.py # Business logic
│       │   └── cache_service.py # Redis caching
│       ├── repository.py        # TimescaleDB queries
│       ├── models.py            # SQLAlchemy models
│       ├── schemas.py           # Pydantic schemas
│       ├── config.py            # Settings
│       └── dependencies.py      # FastAPI dependencies
├── tests/
│   ├── unit/
│   ├── integration/
│   └── performance/
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

### Convenciones

- **Imports**: `from opa_quotes_api.services import QuoteService`
- **Logging**: Structured JSON logs (ver `OPA_Machine/shared/utils/pipeline_logger.py`)
- **Errors**: HTTP status codes estándar + error schemas
- **Tests**: pytest fixtures para TimescaleDB/Redis mock

## 🐛 Troubleshooting

### Error: "Connection to TimescaleDB failed"

```bash
# Verificar que opa-quotes-storage esté operativo
curl http://localhost:5432  # TimescaleDB

# Verificar variables de entorno
echo $TIMESCALE_HOST
echo $TIMESCALE_USER
echo $TIMESCALE_PASSWORD
```

### Error: "Redis connection timeout"

```bash
# Verificar Redis
docker ps | grep redis
redis-cli ping  # Debe responder "PONG"

# Revisar REDIS_URL en .env
cat .env | grep REDIS_URL
```

### Performance Degradado

```bash
# Verificar cache hit rate
curl http://localhost:8000/metrics | grep cache_hit

# Verificar conexiones TimescaleDB
psql -U opa_user -d opa_quotes -c "SELECT count(*) FROM pg_stat_activity;"
```

## 📈 Roadmap

**Fase 1 (Actual)**: MVP REST
- [x] Scaffolding base
- [ ] Implementar routers REST
- [ ] Integrar caching Redis
- [ ] Tests unitarios (>80% coverage)
- [ ] CI/CD con GitHub Actions

**Fase 2**: WebSockets & Optimización
- [x] Implementar WS streaming
- [x] Integración Redis Pub/Sub
- [x] Filtrado multi-ticker
- [x] ConnectionManager
- [x] Cliente HTML ejemplo
- [ ] Heartbeat mechanism
- [ ] Query optimization (TimescaleDB)
- [ ] Rate limiting avanzado
- [ ] Monitoring dashboards (Grafana)

Ver: [ROADMAP.md](ROADMAP.md) para detalles completos.

## 🔗 Referencias

- **Documentación supervisor**: [OPA_Machine/docs/services/module-5-quotes/](https://github.com/Ocaxtar/opa-supervisor/tree/main/docs/services/module-5-quotes)
- **Contratos API**: [OPA_Machine/docs/contracts/apis/](https://github.com/Ocaxtar/opa-supervisor/tree/main/docs/contracts/apis)
- **ADR-007**: Arquitectura multi-workspace
- **Guía de desarrollo**: Ver AGENTS.md

---

**Última actualización**: 2026-01-13  
**Mantenedor**: Equipo OPA
