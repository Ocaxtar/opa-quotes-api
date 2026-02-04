# Database Initialization Scripts

Este directorio contiene scripts de inicialización para TimescaleDB.

## Archivos

- `01-init-timescale.sh` - Script de inicialización automático (Docker entrypoint)
- `02-create-real-time-table.sql` - Script SQL para ejecutar manualmente (OPA-423)

## Uso Automático (Docker)

Los scripts `.sh` se ejecutan automáticamente cuando se crea un nuevo contenedor de TimescaleDB desde el proyecto `opa-quotes-storage`.

## Uso Manual (Base de Datos Existente)

Si la base de datos ya está corriendo y necesitas crear/actualizar la tabla `quotes.real_time`:

```bash
# Desde opa-quotes-storage o donde esté el contenedor TimescaleDB
psql -h localhost -p 5433 -U opa_user -d opa_quotes -f init-db/02-create-real-time-table.sql

# O con Docker
docker exec -i timescaledb_quotes psql -U opa_user -d opa_quotes < init-db/02-create-real-time-table.sql
```

## Schema de quotes.real_time

La tabla sigue el contrato definido en `opa-infrastructure-state/contracts/data-models/quotes.md`:

- **Columnas**: time, ticker, price, change, change_percent, volume, bid, ask, bid_size, ask_size, open, high, low, previous_close, market_cap, pe_ratio, avg_volume_10d, market_status, exchange
- **Hypertable**: Particionada por columna `time`
- **Índices**: ticker+time (DESC), exchange+time (DESC)
- **Política retención**: 90 días (Fase 2), 1 año (Fase 6)

## Troubleshooting

### "relation quotes.real_time does not exist"

Este error (OPA-423) ocurre cuando el servicio `opa-quotes-streamer` intenta escribir a TimescaleDB pero la tabla no existe:

**Solución**:
1. Ejecutar `02-create-real-time-table.sql` manualmente (ver sección "Uso Manual")
2. O recrear el contenedor de TimescaleDB para que ejecute `01-init-timescale.sh`

**Prevención**:
- Asegúrate de que `opa-quotes-storage` esté inicializado antes de habilitar `PUBLISHER_ENABLED` en `opa-quotes-streamer`
