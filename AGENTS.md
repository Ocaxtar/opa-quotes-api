# AGENTS.md - opa-quotes-api

> 🎯 **Guía para agentes IA** - Repositorio operativo del ecosistema OPA_Machine.  
> **Documentación completa**: [Supervisor OPA_Machine](https://github.com/Ocaxtar/OPA_Machine)

---

## 🚦 Pre-Flight Checklist (OBLIGATORIO)

**Antes de cualquier operación**:

| Acción | Recurso | Cuándo |
|--------|---------|--------|
| 🔄 **Sincronizar workspace** | Script `scripts/git/check_sync.sh` | ⚠️ **INICIO DE CADA RUN** |
| Verificar puertos/Docker | [service-inventory.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/infrastructure/service-inventory.md) | ⚠️ Antes de Docker |
| Cargar skill necesario | [Skills INDEX](https://github.com/Ocaxtar/OPA_Machine/blob/main/.github/skills/INDEX.md) | Antes de tarea compleja |
| Trabajar en issue | Skill `git-linear-workflow` | Antes de branch/commit |
| Usar Linear MCP tools | Skill `linear-mcp-tool` | Si tool falla |

### Sincronización Automática

**Al inicio de cada run, ejecutar**:
```bash
bash scripts/git/check_sync.sh
```

**Exit codes**:
- `0`: ✅ Sincronizado (continuar)
- `2`: ⚠️ Commits locales sin push (avisar usuario)
- `3`: ⚠️ Cambios remotos en código (avisar usuario)
- `4`: ❌ Divergencia detectada (requerir resolución manual)
- `5`: ⚠️ No se pudo conectar con remoto

**Pull automático**: Si solo hay cambios en `docs/`, `AGENTS.md`, `.github/skills/`, `README.md`, `ROADMAP.md` → pull automático aplicado.

**Ver detalles completos**: Consultar skill `workspace-sync` en OPA_Machine supervisor.

---

## 📋 Información del Proyecto

**Nombre**: opa-quotes-api  
**Módulo**: Cotización (Módulo 2)  
**Tipo**: api (FastAPI)  
**Fase**: 1  
**Equipo Linear**: OPA  
**Repositorio**: https://github.com/Ocaxtar/opa-quotes-api  
**Puerto asignado**: 8000

### Rol en el Ecosistema

API REST para consulta de cotizaciones. Expone endpoints para obtener precios históricos y en tiempo real desde TimescaleDB.

### Dependencias

| Servicio | Puerto | Propósito |
|----------|--------|-----------|
| TimescaleDB (quotes-storage) | 5433 | Base de datos |
| API | 8000 | Servicio HTTP |

---

## ⚠️ Reglas Críticas

### 1. Prefijo en Comentarios Linear

```
🤖 Agente opa-quotes-api: [mensaje]
```

**Obligatorio** en todo comentario. Auditoría supervisor detecta violaciones.

### 2. Commits con Referencia a Issue

```
❌ git commit -m "Fix bug"
✅ git commit -m "OPA-XXX: Fix bug description"
```

### 3. Puerto DB 5433 (NO 5432)

```
❌ DATABASE_URL=...localhost:5432/... → Conflicto PostgreSQL local
✅ DATABASE_URL=...localhost:5433/... → Puerto correcto
```

### 4. Pre-Done Checklist

Antes de mover issue a Done:
- [ ] Código commiteado y pusheado
- [ ] Tests pasan (si aplica)
- [ ] Comentario de cierre con prefijo
- [ ] Verificar archivos en GitHub web (no solo local)

---

## 🔧 Convenciones

| Elemento | Convención |
|----------|------------|
| Idioma código | Inglés |
| Idioma comentarios | Español |
| Commits | `OPA-XXX: Descripción` |
| Python | 3.12 (NO 3.13) |
| Framework | FastAPI |
| DB Driver | asyncpg |

---

## 📚 Skills Disponibles

| Skill | Propósito |
|-------|-----------|
| `git-linear-workflow` | Workflow Git+Linear |
| `linear-mcp-tool` | Errores MCP Linear |
| `run-efficiency` | Gestión tokens |

> Ver [INDEX.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/.github/skills/INDEX.md) para lista completa.

---

## 🔗 Referencias Supervisor

| Documento | Propósito |
|-----------|-----------|
| [AGENTS.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/AGENTS.md) | Guía maestra |
| [service-inventory.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/infrastructure/service-inventory.md) | Puertos y conflictos |
| [ROADMAP.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/ROADMAP.md) | Fases del proyecto |
| [Contratos](https://github.com/Ocaxtar/OPA_Machine/tree/main/docs/contracts) | APIs y schemas |

---

*Actualizado con workspace-sync skill - OPA-293 - 2026-01-20*
