# AGENTS.md - opa-quotes-api

> 🎯 **Guía específica para agentes IA** en este repo operativo.  
> **Supervisión**: [OPA_Machine/AGENTS.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/AGENTS.md)

---

## 🚦 Pre-Flight Checklist (OBLIGATORIO)

| Acción | Documento/Skill | Cuándo |
|--------|-----------------|--------|
| Consultar infraestructura | [opa-infrastructure-state](https://github.com/Ocaxtar/opa-infrastructure-state/blob/main/state.yaml) | ANTES de Docker/DB/Redis |
| Sincronizar workspace | Skill `workspace-sync` (supervisor) | Inicio sesión |
| Verificar estado repos | [DASHBOARD.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/DASHBOARD.md) | Inicio sesión |
| Trabajar en issue | Skill `git-linear-workflow` | Antes branch/commit |
| Usar Linear MCP | Skill `linear-mcp-tool` | Si tool falla/UUID |

---

## 📋 Info del Repositorio

**Nombre**: opa-quotes-api  
**Tipo**: API REST (FastAPI)  
**Propósito**: Expone endpoints para cotizaciones en tiempo real y datos históricos  
**Puerto**: 8000  
**Team Linear**: OPA  
**Tecnologías**: Python 3.12, FastAPI, SQLAlchemy, Redis (cache)

**Funcionalidad**:
- GET /quotes/stream - SSE stream de cotizaciones real-time
- GET /quotes/historical - Consulta históricos TimescaleDB
- GET /quotes/snapshot - Snapshot actual de un ticker

**Dependencias**:
- opa-quotes-storage (TimescaleDB en puerto 5433)
- opa-quotes-streamer (via Redis canal `quotes:stream`)

---

## ⚠️ Reglas Críticas Específicas

### 1. Puerto PostgreSQL = 5433 (NO 5432)

```
❌ Conectar a localhost:5432
✅ Conectar a localhost:5433
```

**Motivo**: PostgreSQL local Windows ocupa 5432. Ver [service-inventory.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/infrastructure/service-inventory.md).

### 2. Usar opa-infrastructure-state para schemas

```
❌ Asumir estructura DB desde docs conceptuales
✅ Consultar state-db-schemas.yaml.md ANTES de SQLAlchemy
```

**Motivo**: OPA-342 (PKs incorrectas → 0 resultados).

### 3. Cache Redis para todas las queries

```python
# ✅ Patrón obligatorio
@app.get("/quotes/{ticker}")
async def get_quote(ticker: str):
    cache_key = f"quote:{ticker}"
    cached = await redis.get(cache_key)
    if cached:
        return cached
    
    # Query DB solo si no hay cache
    result = db.query(...)
    await redis.setex(cache_key, 60, result)
    return result
```

**TTL**:
- Snapshots: 5s
- Históricos: 300s

---

## 🔄 Workflows Especiales

### Antes de Crear SQLAlchemy Models (OPA-343)

**Al consumir tablas de otros repos**:

1. **CONSULTAR** [state-db-schemas.yaml.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/infrastructure/state-db-schemas.yaml.md) para estructura real
2. Verificar primary_key, tipos de columnas, foreign_keys
3. Crear models basados en docs (no asumir estructura)

**Por qué**: Previene bugs tipo OPA-342 (SQLAlchemy models con PKs incorrectas → queries devuelven 0 resultados).

**Tablas consumidas**:
- `quotes.quotes` (cuando se implemente en opa-quotes-storage)

---

## 🔧 Operaciones de Infraestructura

> **OBLIGATORIO**: Ejecutar ANTES de cualquier operación Docker/DB/Redis.

### Workflow de 3 Pasos

#### Paso 1: Ejecutar Preflight Check

```bash
# Desde este repo
python ../opa-supervisor/scripts/infrastructure/preflight_check.py --module quotes --operation docker-compose
```

#### Paso 2: Evaluar Resultado

| Resultado | Acción |
|-----------|--------|
| ✅ PREFLIGHT PASSED | Continuar con la tarea |
| ❌ PREFLIGHT FAILED | **NO continuar**. Reportar al usuario qué servicios faltan |

#### Paso 3: Configurar usando state.yaml

**Source of Truth**: `opa-infrastructure-state/state.yaml`

```python
# ✅ CORRECTO: Variables de entorno con fallback
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://opa_user:opa_password@localhost:5433/opa_quotes")

# ❌ INCORRECTO: Hardcodear valores
DATABASE_URL = "postgresql://opa_user:opa_password@localhost:5433/opa_quotes"
```

### Anti-Patrones (PROHIBIDO)

| Anti-Patrón | Por qué está mal |
|-------------|------------------|
| ❌ Consultar `service-inventory.md` como fuente | Es documento AUTO-GENERADO, no editable |
| ❌ Hardcodear puertos/credenciales | Dificulta mantenimiento y causa bugs |
| ❌ Asumir que servicio existe sin validar | Causa "Connection refused" en deploy |
| ❌ Usar puerto 5432 para Docker | PostgreSQL local Windows lo ocupa |
| ❌ Continuar si preflight falla | Propaga configuración inválida |

### Quick Reference: Puertos

| Servicio | Puerto | Módulo |
|----------|--------|--------|
| TimescaleDB Quotes | 5433 | Quotes |
| TimescaleDB Capacity | 5434 | Capacity |
| Redis Dev | 6381 | Shared |
| quotes-api | 8000 | Quotes |
| capacity-api | 8001 | Capacity |

> **Source of Truth**: [opa-infrastructure-state/state.yaml](https://github.com/Ocaxtar/opa-infrastructure-state/blob/main/state.yaml)

---

## 🔧 Convenciones

| Elemento | Convención |
|----------|------------|
| **Idioma código** | Inglés |
| **Idioma interacción** | Español |
| **Formato commit** | `OPA-XXX: Descripción imperativa` |
| **Branches** | `username/opa-xxx-descripcion` |
| **Labels issues** | `Feature/Bug` + `opa-quotes-api` |

---

## 🎯 Skills Disponibles (carga bajo demanda)

| Skill | Ubicación | Triggers |
|-------|-----------|----------|
| `git-linear-workflow` | `~/.copilot/skills/` | issue, branch, commit, PR |
| `linear-mcp-tool` | `~/.copilot/skills/` | error Linear, UUID |
| `run-efficiency` | `~/.copilot/skills/` | tokens, context |

**Skills supervisor** (consultar desde [supervisor](https://github.com/Ocaxtar/OPA_Machine)):
- `multi-workspace`, `contract-validator`, `ecosystem-auditor`, `infrastructure-lookup`

---

## 📚 Referencias

| Recurso | URL |
|---------|-----|
| Supervisor AGENTS.md | https://github.com/Ocaxtar/OPA_Machine/blob/main/AGENTS.md |
| opa-infrastructure-state | https://github.com/Ocaxtar/opa-infrastructure-state/blob/main/state.yaml |
| DB Schemas Source of Truth | https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/infrastructure/state-db-schemas.yaml.md |
| Service Inventory | https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/infrastructure/service-inventory.md |
| DASHBOARD | https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/DASHBOARD.md |

---

*Documento sincronizado con supervisor v2.1 (2026-01-26) - OPA-368*
