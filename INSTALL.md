# INSTALL.md

## Instalación y Configuración

### Requisitos Previos

- Python 3.12.x
- Poetry 2.0+
- PostgreSQL 14+ (para desarrollo local) o acceso a TimescaleDB
- Redis 7+ (para caché)

### 1. Clonar el Repositorio

```bash
git clone https://github.com/Ocaxtar/opa-quotes-api.git
cd opa-quotes-api
```

### 2. Instalar Dependencias

```bash
poetry install
```

Esto creará un entorno virtual en `.venv` e instalará todas las dependencias necesarias.

### 3. Configurar Variables de Entorno

Copiar el archivo de ejemplo y ajustar según sea necesario:

```bash
cp .env.example .env
```

Editar `.env` con tus credenciales:

```env
DATABASE_URL=postgresql+asyncpg://opa:opa_password@localhost:5432/quotes
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
API_PORT=8000
```

### 4. Base de Datos (Opcional para desarrollo)

Si necesitas una base de datos local para desarrollo:

```bash
# Usando Docker Compose (recomendado)
docker-compose up -d

# O manualmente con PostgreSQL local
createdb quotes
psql quotes -c "CREATE USER opa WITH PASSWORD 'opa_password';"
psql quotes -c "GRANT ALL PRIVILEGES ON DATABASE quotes TO opa;"
```

### 5. Ejecutar Migraciones (Cuando estén implementadas)

```bash
poetry run alembic upgrade head
```

### 6. Ejecutar la Aplicación

#### Modo Desarrollo

```bash
poetry run python -m opa_quotes_api.dev_server
```

O simplemente:

```bash
poetry run uvicorn opa_quotes_api.main:app --reload --host 0.0.0.0 --port 8000
```

#### Modo Producción

```bash
poetry run uvicorn opa_quotes_api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 7. Verificar la Instalación

Abrir en el navegador:

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Métricas: http://localhost:8000/metrics

### 8. Ejecutar Pruebas

```bash
# Todas las pruebas
poetry run pytest

# Con cobertura
poetry run pytest --cov=opa_quotes_api --cov-report=html

# Solo pruebas unitarias
poetry run pytest -m unit

# Solo pruebas de integración
poetry run pytest -m integration
```

### 9. Linting y Formateo

```bash
# Verificar código
poetry run ruff check .

# Formatear código
poetry run ruff format .

# Type checking
poetry run mypy src/
```

## Docker

### Construir la Imagen

```bash
docker build -t opa-quotes-api:latest .
```

### Ejecutar con Docker Compose

```bash
docker-compose up
```

Esto iniciará:
- La API en el puerto 8000
- PostgreSQL/TimescaleDB en el puerto 5432
- Redis en el puerto 6379

## Solución de Problemas

### Error de Conexión a la Base de Datos

1. Verificar que PostgreSQL está corriendo
2. Verificar credenciales en `.env`
3. Verificar que la URL usa el driver `asyncpg`: `postgresql+asyncpg://...`

### Error de Módulos Faltantes

```bash
poetry install --sync
```

### Problemas con Poetry

```bash
# Limpiar caché
poetry cache clear pypi --all

# Reinstalar
poetry install --no-cache
```

## Configuración del IDE

### VS Code

Se recomienda instalar las siguientes extensiones:
- Python
- Pylance
- Ruff

Configuración recomendada en `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.formatting.provider": "ruff",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```
