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

## 📚 Guías Especializadas (CONSULTAR PRIMERO)

Estas guías del repositorio supervisor contienen instrucciones detalladas que aplican a todos los repositorios del ecosistema:

| Guía | Propósito | Cuándo consultar |
|------|-----------|------------------|
| **[workflow-git-linear.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/workflow-git-linear.md)** | Workflow Git+Linear completo | Al trabajar en issues (branch, commit, merge, cierre) |
| **[multi-workspace-guide.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/multi-workspace-guide.md)** | Arquitectura 20 repos, coordinación | Al crear repos, issues cross-repo, labels Linear |
| **[code-conventions.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/code-conventions.md)** | Estándares código, testing, CI/CD | Al escribir código, configurar tests, Docker |
| **[technology-stack.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/technology-stack.md)** | Stack tecnológico consolidado | Al elegir librerías, evaluar rendimiento |
| **[linear-mcp-quickstart.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/linear-mcp-quickstart.md)** | Errores comunes Linear MCP | Al usar mcp_linear tools (errores, fixes) |

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

## 🛡️ Validación de Convenciones

**REGLA CRÍTICA**: Antes de ejecutar acciones que modifican estado (commits, PRs, issues Done), validar cumplimiento de convenciones.

### Convenciones No Negociables

| Convención | Requisito | Documento |
|------------|-----------|-----------|
| **Commits** | DEBEN incluir referencia a issue (`OPA-XXX`) en mensaje | [workflow-git-linear.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/workflow-git-linear.md) |
| **Issues** | DEBEN crearse en Linear ANTES de implementar fix | [workflow-git-linear.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/workflow-git-linear.md) |
| **Branches** | DEBEN seguir patrón `username/opa-xxx-descripcion` | [workflow-git-linear.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/workflow-git-linear.md) |
| **PRs** | DEBEN enlazar a issue en descripción | [workflow-git-linear.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/workflow-git-linear.md) |
| **Issues Done** | DEBEN tener tests ejecutados y pasando | [code-conventions.md](https://github.com/Ocaxtar/OPA_Machine/blob/main/docs/guides/code-conventions.md) |

## 📝 Regla Crítica: Comentarios vs Descripción en Issues

**PRINCIPIO**: La **descripción** de una issue es la **especificación inicial**. Los **comentarios** son el **registro de progreso**.

**Comportamiento requerido**:

| Acción | Tool Correcta | Tool Incorrecta |
|--------|---------------|-----------------|
| Reportar avance parcial | `mcp_linear_create_comment()` | ❌ `mcp_linear_update_issue(body=...)` |
| Reactivar issue cerrada | `mcp_linear_create_comment()` + `update_issue(state="In Progress")` | ❌ Solo modificar descripción |
| Documentar error encontrado | `mcp_linear_create_comment()` | ❌ Editar descripción |
| Añadir diagnóstico | `mcp_linear_create_comment()` | ❌ Modificar descripción |
| Cerrar con resumen | `mcp_linear_create_comment()` + `update_issue(state="Done")` | ❌ Solo cambiar estado |

**¿Por qué?**:
- **Trazabilidad**: Comentarios tienen timestamps automáticos → historial auditable
- **Notificaciones**: Comentarios notifican a watchers → mejor colaboración
- **Reversibilidad**: Descripción original preservada → contexto no se pierde
- **Multi-agente**: Varios agentes pueden comentar sin conflictos de edición

## ⚠️ Validación Pre-cierre de Issue (CRÍTICO)

**REGLA DE ORO**: Si un archivo NO está en GitHub en rama `main`, la issue NO está "Done".

### Checklist OBLIGATORIO antes de mover issue a "Done"

```bash
# 0. LEER COMENTARIOS DE LA ISSUE (PRIMERO)
# - Revisar TODOS los comentarios (especialmente los más recientes)
# - Verificar que no hay instrucciones contradictorias

# 1. Verificar estado de git
git status  # Debe estar limpio

# 2. Confirmar que archivos mencionados en la issue EXISTEN
ls ruta/al/archivo-nuevo.md

# 3. Commitear con mensaje correcto
git add [archivos]
git commit -m "OPA-XXX: Descripción clara"

# 4. Pushear a GitHub
git push origin main
# O si trabajas en rama:
git push origin <nombre-rama>

# 5. VERIFICAR en GitHub web que commit aparece

# 6. Si trabajaste en rama feature: MERGEAR a main
git checkout main
git pull origin main
git merge --squash <nombre-rama>
git commit -m "OPA-XXX: Descripción completa"
git push origin main

# 7. Eliminar branch (local + remota)
git branch -d <nombre-rama>
git push origin --delete <nombre-rama> 2>/dev/null || true

# 8. Solo ENTONCES: Mover issue a "Done" en Linear
```

### Template de Comentario Final

TODO cierre de issue DEBE incluir comentario con este formato:

```markdown
## ✅ Resolución

🤖 **Agente opa-quotes-api**

**Pre-checks**:
- [x] Leídos TODOS los comentarios de la issue
- [x] Verificadas dependencias mencionadas (si hay)

**Cambios realizados**:
- [x] Archivo X creado/modificado
- [x] Archivo Y actualizado

**Commits**:
- Hash: abc1234
- Mensaje: "OPA-XXX: Descripción"
- Link: https://github.com/Ocaxtar/opa-quotes-api/commit/abc1234

**Verificación**:
- [x] Archivos confirmados en `git status`
- [x] Commit pusheado a GitHub
- [x] Rama mergeada a `main`
- [x] Archivos visibles en GitHub web en rama `main`

**Tests** (si aplica):
- [x] pytest pasado (X/Y tests)
- [x] Linter sin errores

Issue cerrada.
```

### Errores Comunes que Causan Pérdida de Trabajo

| Error | Consecuencia | Solución |
|-------|--------------|----------|
| ❌ Cerrar issue sin verificar archivos en `main` | Trabajo perdido en rama sin mergear | Siempre verificar en GitHub web |
| ❌ Pushear a rama pero NO mergear a main | Código no desplegable | Siempre mergear rama a `main` |
| ❌ Commitear pero NO pushear | Archivos solo en local | `git push` SIEMPRE antes de cerrar |
| ❌ Asumir que archivos están commiteados | Archivos solo en working directory | `git status` debe estar limpio |
| ❌ Cerrar issue sin comentario final | Sin trazabilidad | Template SIEMPRE |

### Prefijo Obligatorio en Comentarios

**TODO comentario en Linear DEBE tener prefijo**:

```
🤖 Agente opa-quotes-api: [tu mensaje]
```

**Violaciones detectadas por auditoría supervisor**:
- Issue sin comentario → REABIERTA
- Comentario sin prefijo → Backfill correctivo

---

📝 **Fecha sincronización normativa**: 2026-01-14  
**Versión normativa**: 1.0.0