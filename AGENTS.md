# AGENTS.md - opa-quotes-api

> 🎯 **Guía para agentes IA** - Repositorio operativo del ecosistema OPA_Machine.  
> **Documentación completa**: [Supervisor OPA_Machine](https://github.com/Ocaxtar/opa-supervisor)

---

## 🚦 Pre-Flight Checklist (OBLIGATORIO)

**Antes de cualquier operación**:

| Acción | Recurso | Cuándo |
|--------|---------|--------|
| 🔄 **Sincronizar workspace** | Script `scripts/git/check_sync.sh` (incluye activación MCP) | ⚠️ **INICIO DE CADA RUN** |
| Verificar puertos/Docker | [service-inventory.md](https://github.com/Ocaxtar/opa-supervisor/blob/main/docs/infrastructure/service-inventory.md) | ⚠️ Antes de Docker |
| Consultar infraestructura | [opa-infrastructure-state](https://github.com/Ocaxtar/opa-infrastructure-state) | ⚠️ Antes de Docker/DB/Redis |
| Cargar skill necesario | Skills globales en `~/.copilot/skills/` | Antes de tarea compleja |
| Trabajar en issue | Skill global `git-linear-workflow` | Antes de branch/commit |
| Usar Linear MCP tools | Skill global `linear-mcp-tool` | Si tool falla/necesitas categorías extra |

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

**Pull automático**: Si solo hay cambios en `docs/`, `AGENTS.md`, `README.md`, `ROADMAP.md` → pull automático aplicado.

**Activación MCP incluida**: El skill `workspace-sync` del supervisor OPA_Machine activa automáticamente los grupos principales de MCP tools (Linear Issues, Workspace Overview, GitHub Repos, GitHub Issues). Si necesitas tools de categorías adicionales (documentos, tracking, team management, PR reviews), actívalas bajo demanda.

**Ver detalles completos**: Consultar skill `workspace-sync` en opa-supervisor.

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

**Skills Globales** (ubicación: `~/.copilot/skills/`):

| Skill | Propósito |
|-------|-----------|
| `git-linear-workflow` | Workflow Git+Linear completo |
| `linear-mcp-tool` | Errores MCP Linear y soluciones |
| `run-efficiency` | Gestión tokens, pre-Done checklist |

> ⚠️ **Nota**: Skills ya no tienen carpeta local `.github/skills/`. Están centralizados en ubicación global del usuario.

**Skills OPA específicos**: Ver [opa-supervisor/.github/skills/](https://github.com/Ocaxtar/opa-supervisor/tree/main/.github/skills) para skills de arquitectura, auditoría y transición de fases.

---

## 🔗 Referencias Supervisor

| Documento | Propósito |
|-----------|-----------|
| [AGENTS.md](https://github.com/Ocaxtar/opa-supervisor/blob/main/AGENTS.md) | Guía maestra |
| [service-inventory.md](https://github.com/Ocaxtar/opa-supervisor/blob/main/docs/infrastructure/service-inventory.md) | Puertos y conflictos |
| [opa-infrastructure-state](https://github.com/Ocaxtar/opa-infrastructure-state) | Estado infraestructura |
| [ROADMAP.md](https://github.com/Ocaxtar/opa-supervisor/blob/main/ROADMAP.md) | Fases del proyecto |
| [Contratos](https://github.com/Ocaxtar/opa-supervisor/tree/main/docs/contracts) | APIs y schemas |

---

*Actualizado OPA-298: Skills migrados a ubicación global - 2026-01-21*
