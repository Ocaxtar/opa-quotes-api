# AGENTS.md - Guía para Agentes de IA

## Información del Repositorio

**Nombre**: opa-quotes-api  
**Función**: FastAPI REST + WebSockets para servir cotizaciones en tiempo real  
**Módulo**: 5 (Cotización)  
**Tipo**: API Service  
**Fase**: 1 (Desarrollo Inicial)  
**Repositorio GitHub**: https://github.com/Ocaxtar/opa-quotes-api  
**Proyecto Linear**: opa-quotes-api  
**Label Linear**: `opa-quotes-api` (sub-tag del grupo "repo")

## Contexto del Módulo

Este repositorio es parte del **Módulo 5 (Cotización)**, uno de los 5 módulos core del ecosistema OPA_Machine. El módulo completo consta de:

1. **opa-quotes-streamer** (Rust) → Ingestión streaming tiempo real
2. **opa-quotes-storage** (Python) → Almacenamiento TimescaleDB
3. **opa-quotes-api** (Python) → **ESTE REPOSITORIO** → API REST + WebSockets

**Responsabilidad de este servicio**: Exponer datos de cotizaciones mediante API REST y streaming WebSocket para consumo de módulos downstream (Capacidad, Predicción).

## Stack Tecnológico

| Categoría | Tecnología | Versión | Rationale |
|-----------|------------|---------|-----------|
| Framework | FastAPI | 0.104+ | API async de alto rendimiento, OpenAPI automático |
| ORM | SQLAlchemy | 2.0+ | ORM maduro con soporte async para TimescaleDB |
| DB Driver | psycopg2-binary | 2.9+ | Driver PostgreSQL estable |
| Cache | Redis (redis-py) | 7+ | Caching de última cotización (TTL 5s) |
| WebSockets | websockets | 12+ | Streaming asíncrono para clientes real-time |
| Validation | Pydantic | 2.5+ | Validación de schemas y serialización |
| Testing | pytest + pytest-asyncio | 7.4+ | Tests async para FastAPI |
| Monitoring | prometheus-client | 0.18+ | Métricas personalizadas |

**Decisiones clave**:
- **FastAPI**: 3-5x más rápido que Flask, typing nativo, async/await first-class
- **Redis**: Cache TTL 5s para reducir carga en TimescaleDB
- **Pydantic v2**: 5-50x más rápido que v1 en serialización

## Arquitectura del Servicio

### Flujo de Datos

```
Cliente (curl/SDK)
      │
      ├─► GET /quotes/{ticker}/latest
      ├─► GET /quotes/{ticker}/history
      └─► POST /quotes/batch
            │
            ▼
      [FastAPI Router]
            │
            ▼
      [Quote Service]
         │        │
         ▼        ▼
    [Cache]  [Repository]
    (Redis)   (TimescaleDB)
         │        │
         └────┬───┘
              ▼
         Response JSON
```

### Componentes

**1. Routers** (`routers/quotes.py`):
- Endpoints REST estandarizados
- Validación de parámetros con Pydantic
- Manejo de errores HTTP

**2. Services** (`services/quote_service.py`):
- Lógica de negocio (check cache → query DB)
- Agregaciones (OHLC en intervalos)
- Transformaciones de datos

**3. Cache** (`services/cache_service.py`):
- Redis con TTL 5 segundos
- Key pattern: `quote:{ticker}:latest`
- Invalidación on-demand

**4. Repository** (`repository.py`):
- Abstracción queries TimescaleDB
- Query optimization (time_bucket, índices)
- Connection pooling

**5. Models** (`models.py`):
- SQLAlchemy models para `quotes.real_time`
- Mapeo a hypertable de TimescaleDB

**6. Schemas** (`schemas.py`):
- Pydantic schemas para request/response
- Validación de payloads

## 🔧 Gestión de Tools MCP

### Activación de Tools Linear/GitHub

Algunas herramientas MCP (Model Context Protocol) requieren activación explícita antes de usarse. **SIEMPRE** activa las tools necesarias al inicio de tu trabajo con este repositorio.

#### Tools que Requieren Activación

| Tool Category | Activation Function | Tools Incluidas |
|---------------|---------------------|-----------------|
| Issue Management | `activate_issue_management_tools()` | `mcp_linear_create_comment`, `mcp_linear_create_issue`, `mcp_linear_create_issue_label`, `mcp_linear_create_project`, `mcp_linear_update_issue` |
| Repository Management | `activate_repository_management_tools()` | `mcp_github_create_branch`, `mcp_github_create_pull_request`, `mcp_github_merge_pull_request`, etc. |
| Pull Request Review | `activate_pull_request_review_tools()` | `mcp_github_add_comment_to_pending_review`, `mcp_github_pull_request_review_write`, etc. |

#### Workflow de Activación

```python
# Al inicio de trabajo con Linear
<invoke name="activate_issue_management_tools" />

# Al trabajar con GitHub PRs
<invoke name="activate_repository_management_tools" />

# Al revisar PRs
<invoke name="activate_pull_request_review_tools" />
```

#### Patrón de Uso Seguro

**✅ CORRECTO**:
1. Detectar necesidad de tool (ej: crear comentario en Linear)
2. Activar categoría de tools
3. Usar tool específico

**❌ INCORRECTO**:
1. Intentar usar tool sin activar
2. Recibir error "Tool not found"
3. Continuar sin completar acción

#### Manejo de Errores

Si recibes `Tool not found or not activated`:
1. **NO continues** sin completar la acción
2. Activa la categoría de tools correspondiente
3. **Reintenta** la operación
4. Si persiste error, devuelve control al usuario

### Tools Siempre Disponibles

Estas tools NO requieren activación:
- `mcp_linear_get_issue`, `mcp_linear_list_comments`, `mcp_linear_list_issues`
- `file_search`, `grep_search`, `read_file`, `replace_string_in_file`
- `run_in_terminal`, `get_terminal_output`
- Git commands via terminal

## 🛡️ Validación de Convenciones

### Checkpoint Pre-Acción

Antes de ejecutar acciones críticas, **VALIDA** que cumples las convenciones de este repositorio:

#### ✅ Pre-Commit Checklist

- [ ] **Mensaje de commit** incluye identificador de issue (ej: `OPA-232: ...`)
- [ ] **Branch** sigue convención: `oscarcalvo/OPA-XXX-descripcion-corta`
- [ ] **Tests** pasan localmente (`poetry run pytest`)
- [ ] **Linter** sin errores
- [ ] **Issue en Linear** existe y está en estado correcto

#### ✅ Pre-Issue Close Checklist

- [ ] **Comentario de cierre** añadido con prefijo `🤖 Agente opa-quotes-api:`
- [ ] **Pre-checks** documentados en comentario
- [ ] **Problema identificado** explicado
- [ ] **Solución implementada** detallada
- [ ] **Commits** referenciados con hash y link
- [ ] **Verificación** realizada y documentada
- [ ] **Branch mergeada** y eliminada (local + remota)

#### ✅ Pre-PR Checklist

- [ ] **Título** incluye identificador de issue
- [ ] **Descripción** explica cambios y rationale
- [ ] **Tests** incluidos para nuevas features
- [ ] **Docs** actualizadas si API cambió

### Detección de Violaciones

Si detectas que estás a punto de violar una convención:

1. **DETENTE** inmediatamente
2. **INFORMA** al usuario del problema detectado
3. **SUGIERE** corrección
4. **ESPERA** confirmación del usuario antes de continuar

**Ejemplo**:
```
⚠️ DETECCIÓN DE VIOLACIÓN

Convención: "Commits DEBEN referenciar issue Linear"
Acción planeada: git commit -m "Fix bug"
Problema: Mensaje sin identificador OPA-XXX

¿Deseas que corrija el mensaje a "OPA-232: Fix bug"?
```

### Recuperación ante Violaciones

Si ya violaste una convención:

1. **RECONOCE** el error
2. **CORRIGE** si es posible:
   - Commit sin issue: `git commit --amend -m "OPA-XXX: ..."`
   - Issue cerrado sin comentario: Añadir comentario retroactivamente
   - Branch sin mergear: `git checkout main && git merge --squash ...`
3. **DOCUMENTA** la corrección en Linear/GitHub

## Flujo de Trabajo de Desarrollo

### 1. Setup Inicial

```bash
# Clonar repositorio
git clone https://github.com/Ocaxtar/opa-quotes-api.git
cd opa-quotes-api

# Crear entorno virtual con Poetry
poetry install

# Configurar variables de entorno
cp .env.example .env
# Editar .env con credenciales TimescaleDB y Redis

# Levantar servicios locales (Redis)
docker-compose up -d

# Verificar conectividad
poetry run python -c "from opa_quotes_api.dependencies import get_db; print('DB OK')"
poetry run python -c "import redis; r=redis.Redis(host='localhost'); print(r.ping())"
```

### 2. Implementar Feature

**Workflow típico**:

```bash
# 1. Crear rama desde main
git checkout -b oscarcalvo/OPA-XXX-feature-name

# 2. Crear router endpoint
# Editar: src/opa_quotes_api/routers/quotes.py

@router.get("/quotes/{ticker}/latest", response_model=QuoteResponse)
async def get_latest_quote(
    ticker: str,
    service: QuoteService = Depends(get_quote_service)
):
    quote = await service.get_latest(ticker)
    if not quote:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return quote

# 3. Implementar servicio
# Editar: src/opa_quotes_api/services/quote_service.py

async def get_latest(self, ticker: str) -> Optional[QuoteResponse]:
    # Check cache
    cached = await self.cache.get(f"quote:{ticker}:latest")
    if cached:
        return QuoteResponse.model_validate_json(cached)
    
    # Query DB
    quote = await self.repository.get_latest(ticker)
    if quote:
        # Cache result
        await self.cache.set(
            f"quote:{ticker}:latest",
            quote.model_dump_json(),
            ex=5  # TTL 5 segundos
        )
    return quote

# 4. Añadir tests
poetry run pytest tests/unit/test_quote_service.py -v

# 5. Commit con convención
git add .
git commit -m "OPA-XXX: Implement GET /quotes/{ticker}/latest endpoint"
git push origin oscarcalvo/OPA-XXX-feature-name
```

### 3. Testing

**Tests unitarios** (mock Redis + TimescaleDB):
```python
# tests/unit/test_quote_service.py
@pytest.mark.asyncio
async def test_get_latest_quote_from_cache(mock_cache, mock_repository):
    service = QuoteService(cache=mock_cache, repository=mock_repository)
    quote = await service.get_latest("AAPL")
    
    assert quote.ticker == "AAPL"
    mock_cache.get.assert_called_once_with("quote:AAPL:latest")
    mock_repository.get_latest.assert_not_called()  # Cache hit
```

**Tests de integración** (TimescaleDB + Redis reales):
```python
# tests/integration/test_quotes_api.py
@pytest.mark.asyncio
async def test_get_latest_quote_integration(test_client, timescale_db, redis_db):
    # Seed data
    await timescale_db.insert_quote("AAPL", timestamp=..., close=150.90)
    
    # Request
    response = test_client.get("/quotes/AAPL/latest")
    
    assert response.status_code == 200
    assert response.json()["ticker"] == "AAPL"
    assert response.json()["close"] == 150.90
```

**Ejecutar tests**:
```bash
# Solo unitarios (fast)
poetry run pytest tests/unit/ -v

# Integración (requiere Docker)
docker-compose -f docker-compose.test.yml up -d
poetry run pytest tests/integration/ -v

# Con coverage
poetry run pytest --cov=opa_quotes_api --cov-report=html
```

### 4. Manejo de Issues en Linear

**Antes de empezar**:
```bash
# 1. Leer issue completa en Linear (incluir TODOS los comentarios)
# 2. Verificar label `opa-quotes-api` presente
# 3. Mover a "In Progress"
```

**Al completar - Workflow de Merge (OBLIGATORIO)**:

```bash
# 1. Asegurar que todos los cambios están commiteados
git status  # Debe estar limpio

# 2. Actualizar main local
git checkout main
git pull origin main

# 3. Mergear branch a main (squash para historia limpia)
git merge --squash oscarcalvo/OPA-XXX-feature-name

# 4. Commit final con mensaje de issue
git commit -m "OPA-XXX: Descripción completa de la feature/fix"

# 5. Pushear a GitHub
git push origin main

# 6. Eliminar branch local y remota
git branch -d oscarcalvo/OPA-XXX-feature-name
git push origin --delete oscarcalvo/OPA-XXX-feature-name 2>/dev/null || true

# 7. IMPORTANTE: Añadir comentario de cierre en Linear con acciones realizas y prefijo 🤖 Agente opa-quotes-api: 
# 8. Solo ENTONCES: Mover a "Done"
```

**⚠️ REGLA CRÍTICA**: NO cerrar issue si la branch no está mergeada. Ramas sin mergear = trabajo perdido.

**Template de comentario de cierre**:
```markdown
🤖 Agente opa-quotes-api: Issue resuelta

**Pre-checks**:
- [x] Leídos TODOS los comentarios
- [x] Verificadas dependencias mencionadas
- [x] Sin instrucciones contradictorias

**Cambios realizados**:
- [x] Implementado endpoint GET /quotes/{ticker}/latest
- [x] Añadido caching Redis (TTL 5s)
- [x] Tests unitarios (12 OK, 90% coverage)

**Commits**:
- Hash: abc1234
- Mensaje: "OPA-XXX: Implement GET /quotes/{ticker}/latest endpoint"
- Link: https://github.com/Ocaxtar/opa-quotes-api/commit/abc1234

**Verificación**:
- [x] pytest pasado (12/12 tests)
- [x] Linter sin errores
- [x] Commit pusheado a GitHub
- [x] Branch mergeada y eliminada

Issue cerrada.
```

## Convenciones del Repositorio

### Nomenclatura

**Archivos**:
- `snake_case.py` para módulos
- `PascalCase` para clases
- `UPPER_CASE.md` para docs root

**Funciones/Variables**:
```python
# ✅ Correcto
async def get_latest_quote(ticker: str) -> QuoteResponse:
    cache_key = f"quote:{ticker}:latest"
    
# ❌ Incorrecto
async def GetLatestQuote(Ticker: str):  # PascalCase en función
    CacheKey = ...  # PascalCase en variable
```

**Imports**:
```python
# ✅ Correcto (absolutos desde package root)
from opa_quotes_api.services import QuoteService
from opa_quotes_api.models import RealTimeQuote

# ❌ Incorrecto (relativos)
from ..services import QuoteService
from .models import RealTimeQuote
```

### Git Workflow

**Mensajes de commit**:
```bash
# Formato: OPA-XXX: <verbo imperativo> <descripción>

✅ "OPA-188: Implement GET /quotes/{ticker}/latest endpoint"
✅ "OPA-189: Add Redis caching for last quote"
✅ "OPA-190: Fix race condition in WebSocket heartbeat"

❌ "Added endpoint"  # Sin identificador Linear
❌ "OPA-188: se implementó el endpoint"  # No imperativo
❌ "OPA-188: implemented the endpoint for getting latest quotes and also added caching"  # Demasiado largo
```

**Ramas**:
```bash
# Formato: {username}/OPA-{id}-{descripcion-corta}
git checkout -b oscarcalvo/OPA-188-latest-quote-endpoint
```

## Testing Patterns

### 1. Tests Unitarios (Mock Dependencies)

```python
# tests/unit/test_quote_service.py
import pytest
from unittest.mock import AsyncMock, Mock

@pytest.fixture
def mock_cache():
    cache = AsyncMock()
    cache.get.return_value = None  # Cache miss
    return cache

@pytest.fixture
def mock_repository():
    repo = AsyncMock()
    repo.get_latest.return_value = QuoteResponse(
        ticker="AAPL",
        timestamp="2025-12-22T10:30:00Z",
        close=150.90
    )
    return repo

@pytest.mark.asyncio
async def test_get_latest_quote_cache_miss(mock_cache, mock_repository):
    service = QuoteService(cache=mock_cache, repository=mock_repository)
    quote = await service.get_latest("AAPL")
    
    assert quote.ticker == "AAPL"
    mock_repository.get_latest.assert_called_once_with("AAPL")
    mock_cache.set.assert_called_once()  # Cached after query
```

### 2. Tests de Integración (DB Real)

```python
# tests/integration/test_quotes_api.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from opa_quotes_api.main import app
from opa_quotes_api.models import RealTimeQuote

@pytest.fixture(scope="session")
def timescale_engine():
    # Usar docker-compose.test.yml
    return create_engine("postgresql://test_user:test_pass@localhost:5433/test_db")

@pytest.mark.asyncio
async def test_get_latest_quote_integration(timescale_engine):
    # Seed data
    with timescale_engine.connect() as conn:
        conn.execute(
            RealTimeQuote.__table__.insert(),
            {"ticker": "AAPL", "timestamp": "2025-12-22 10:30:00", "close": 150.90}
        )
    
    # Test endpoint
    client = TestClient(app)
    response = client.get("/quotes/AAPL/latest")
    
    assert response.status_code == 200
    assert response.json()["close"] == 150.90
```

## Contratos de Integración

### Upstream: opa-quotes-storage

**Contrato**: Acceso lectura-only a `quotes.real_time`

```python
# Query esperada para última cotización
SELECT ticker, timestamp, open, high, low, close, volume, bid, ask
FROM quotes.real_time
WHERE ticker = %(ticker)s
ORDER BY timestamp DESC
LIMIT 1
```

**Índices requeridos**:
- `idx_ticker_timestamp` en `(ticker, timestamp DESC)`

### Downstream: Módulos Consumidores

**opa-capacity-compute**: Consume históricos para análisis MIPL  
**opa-prediction-features**: Consume para feature engineering

**Contrato API**:
- Ver: `OPA_Machine/docs/contracts/apis/quotes-api-contract.md`
- Schemas Pydantic deben ser compatibles con contratos

## Troubleshooting

### Error: "Connection to TimescaleDB refused"

```bash
# Verificar que opa-quotes-storage esté operativo
docker ps | grep timescale

# Verificar variables de entorno
cat .env | grep TIMESCALE

# Test de conexión manual
psql -h localhost -U opa_user -d opa_quotes -c "SELECT 1"
```

### Error: "Redis connection timeout"

```bash
# Verificar Redis operativo
docker ps | grep redis
redis-cli ping  # Debe responder "PONG"

# Verificar configuración
cat .env | grep REDIS_URL
```

### Performance degradado

```bash
# Verificar cache hit rate
curl http://localhost:8000/metrics | grep cache_hit_rate

# Verificar slow queries en TimescaleDB
psql -U opa_user -d opa_quotes -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10"

# Verificar conexiones abiertas
psql -U opa_user -d opa_quotes -c "SELECT count(*) FROM pg_stat_activity"
```

## Métricas y Monitorización

### Prometheus Metrics

```python
# src/opa_quotes_api/metrics.py
from prometheus_client import Counter, Histogram

quote_requests_total = Counter(
    'quote_requests_total',
    'Total de requests de cotizaciones',
    ['ticker', 'endpoint']
)

quote_latency_seconds = Histogram(
    'quote_latency_seconds',
    'Latencia de requests',
    ['endpoint']
)

cache_hits_total = Counter(
    'cache_hits_total',
    'Total de cache hits',
    ['ticker']
)
```

### Logging

```python
# Usar pipeline_logger del supervisor
from shared.utils.pipeline_logger import PipelineLogger

logger = PipelineLogger(
    pipeline_name="opa-quotes-api",
    repository="opa-quotes-api"
)

logger.log_info("Quote request received", extra={"ticker": "AAPL"})
logger.log_error("Cache miss", extra={"ticker": "AAPL"})
```

## Referencias

**Supervisor**:
- Arquitectura: `OPA_Machine/docs/architecture/ecosystem-overview.md`
- Contratos: `OPA_Machine/docs/contracts/apis/quotes-api-contract.md`

**Repos relacionados**:
- [opa-quotes-storage](https://github.com/Ocaxtar/opa-quotes-storage)
- [opa-quotes-streamer](https://github.com/Ocaxtar/opa-quotes-streamer)

---

📝 **Este documento debe actualizarse conforme evolucione el repositorio**  
**Última sincronización con supervisor**: 2025-12-22
