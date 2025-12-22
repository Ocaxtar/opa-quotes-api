# GitHub Actions CI/CD

Este repositorio utiliza GitHub Actions para CI/CD automatizado.

## Workflows

### 1. CI (`ci.yml`)
Ejecuta en cada push y pull request a `main`:

- **Lint**: Valida código con ruff (linter + formatter)
- **Test**: Ejecuta pytest con cobertura
  - Redis service container para tests de integración
  - Upload de cobertura a Codecov
- **Type Check**: Valida tipos con mypy

### 2. Security (`security.yml`)
Ejecuta en push, PR y semanalmente:

- **Security Scan**: 
  - Bandit para detección de vulnerabilidades
  - Safety para chequeo de dependencias

### 3. Release (`release.yml`)
Ejecuta automáticamente al crear tags `v*.*.*`:

- Build del paquete con Poetry
- Creación de GitHub Release
- Publicación a PyPI (opcional)

## Variables Requeridas

### Secrets de GitHub
- `CODECOV_TOKEN`: Token para upload de cobertura (opcional)
- `PYPI_TOKEN`: Token para publicación a PyPI (opcional)

## Uso Local

### Ejecutar linting
```bash
poetry run ruff check src/
poetry run ruff format --check src/
```

### Ejecutar tests con coverage
```bash
docker-compose up -d redis
poetry run pytest -v --cov=opa_quotes_api --cov-report=term-missing
```

### Ejecutar type checking
```bash
poetry run mypy src/ --ignore-missing-imports
```

### Ejecutar security scan
```bash
poetry run bandit -r src/
poetry run safety check
```

## Status Badges

Agregar al README.md:

```markdown
![CI](https://github.com/Ocaxtar/opa-quotes-api/workflows/CI/badge.svg)
![Security](https://github.com/Ocaxtar/opa-quotes-api/workflows/Security/badge.svg)
[![codecov](https://codecov.io/gh/Ocaxtar/opa-quotes-api/branch/main/graph/badge.svg)](https://codecov.io/gh/Ocaxtar/opa-quotes-api)
```

## Configuración de Branches

Se recomienda configurar branch protection rules en GitHub:

1. Ir a Settings → Branches → Add rule
2. Aplicar a `main`
3. Configurar:
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - Seleccionar: `lint`, `test`, `type-check`
   - ✅ Require pull request reviews before merging (1 reviewer)
   - ✅ Dismiss stale pull request approvals when new commits are pushed

## Flujo de Trabajo

1. Crear feature branch: `git checkout -b oscarcalvo/OPA-XXX-feature`
2. Desarrollar y commit
3. Push: `git push origin oscarcalvo/OPA-XXX-feature`
4. Crear Pull Request en GitHub
5. CI ejecuta automáticamente (lint, test, type-check)
6. Merge a main cuando CI pasa y hay aprobación
7. Workflows de main ejecutan automáticamente
