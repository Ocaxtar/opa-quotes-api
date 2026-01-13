# ECOSYSTEM_CONTEXT.md - opa-quotes-api

## Posición en el Ecosistema

Este servicio es la **API REST** del **Módulo 5 (Cotización)**, responsable de exponer cotizaciones de mercado mediante endpoints REST y WebSockets para consumo de módulos downstream.

```
                            ┌─────────────────────────────────────┐
                            │       OPA_Machine (Supervisor)      │
                            │  Documentación, ADRs, Contratos     │
                            └──────────────────┬──────────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
         ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
         │  Módulo 1        │       │  Módulo 5        │       │  Módulo 4        │
         │  Capacidad       │       │  Cotización      │       │  Predicción      │
         └──────────────────┘       └────────┬─────────┘       └──────────────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
                    ▼                        ▼                        ▼
         ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
         │ quotes-streamer  │────▶│  quotes-storage  │────▶│   quotes-api     │
         │   (upstream)     │     │   (upstream)     │     │  ★ ESTE REPO ★   │
         └──────────────────┘     └──────────────────┘     └──────────────────┘
               yfinance                TimescaleDB              FastAPI REST
```

## Flujo de Datos

1. **Entrada** (desde `opa-quotes-storage`):
   - Conexión SQL directa a TimescaleDB
   - Queries optimizadas con índices temporales
   - Cache Redis (TTL 5s) para última cotización

2. **Procesamiento**:
   - Validación de tickers con Pydantic
   - Agregaciones OHLC en intervalos
   - Transformaciones para respuestas JSON

3. **Salida** (hacia clientes y módulos downstream):
   - REST: `GET /quotes/{ticker}/latest`, `GET /quotes/{ticker}/history`
   - Batch: `POST /quotes/batch` (storage API)
   - WebSocket: Streaming real-time (Fase 2)

## Dependencias

### Upstream (fuentes de datos)
| Servicio | Tipo | Descripción |
|----------|------|-------------|
| `opa-quotes-storage` | SQL | Lee quotes de TimescaleDB |
| Redis | Cache | TTL 5s para última cotización |

### Downstream (consumidores)
| Servicio | Tipo | Descripción |
|----------|------|-------------|
| `opa-capacity-compute` | HTTP (futuro) | Consume historial para Event Vectors |
| `opa-prediction-features` | HTTP (futuro) | Feature engineering desde precios |
| Clientes externos | HTTP/WS | SDKs, dashboards |

## Contratos Relevantes

- **API Quotes**: `OPA_Machine/docs/contracts/apis/quotes/quotes-api.yaml`
- **Batch Endpoint**: `OPA_Machine/docs/contracts/apis/quotes/quotes-batch.md`
- **Modelo Datos**: `OPA_Machine/docs/contracts/data-models/quotes.md`

## Repositorio Supervisor

**URL**: https://github.com/Ocaxtar/OPA_Machine

Consultar para:
- ADRs globales (`docs/adr/`)
- Contratos actualizados (`docs/contracts/`)
- Guías de desarrollo (`docs/guides/`)
- ROADMAP global (`ROADMAP.md`)

---

📝 **Última sincronización con supervisor**: 2026-01-13
