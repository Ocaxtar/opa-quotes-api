# Docker Compose Configuration

Este directorio contiene las configuraciones de Docker Compose para desarrollo y testing.

## Archivos

- `docker-compose.yml` - Configuración para desarrollo local
- `docker-compose.test.yml` - Configuración para tests de integración
- `init-db/01-init-timescale.sh` - Script de inicialización de TimescaleDB

## Uso

### Desarrollo Local

```bash
# Levantar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Verificar estado
docker-compose ps

# Detener servicios
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v
```

### Testing

```bash
# Levantar servicios de test
docker-compose -f docker-compose.test.yml up -d

# Ejecutar tests
poetry run pytest

# Limpiar
docker-compose -f docker-compose.test.yml down -v
```

## Servicios

### Redis
- **Puerto**: 6379 (dev) / 6380 (test)
- **Persistencia**: AOF enabled (dev) / tmpfs (test)
- **Health check**: `redis-cli ping`

### PostgreSQL + TimescaleDB
- **Puerto**: 5432 (dev) / 5433 (test)
- **Usuario**: opa / test_user
- **Database**: quotes / test_quotes
- **Health check**: `pg_isready`

### API
- **Puerto**: 8000
- **Hot reload**: Enabled en desarrollo
- **Dependencias**: Espera health checks de Redis y PostgreSQL

## Volúmenes

Los datos persisten en volúmenes Docker:
- `postgres_data` - Datos de PostgreSQL
- `redis_data` - Datos de Redis

Para limpiar todos los datos:
```bash
docker-compose down -v
```

## Inicialización de Base de Datos

El script `init-db/01-init-timescale.sh` se ejecuta automáticamente al crear el contenedor de PostgreSQL y:

1. Crea la extensión TimescaleDB
2. Crea el schema `quotes`
3. Crea la tabla `quotes.real_time`
4. Convierte la tabla a hypertable (particionamiento por tiempo)
5. Crea índices optimizados

## Variables de Entorno

Las configuraciones se pueden sobrescribir creando un archivo `.env`:

```env
DATABASE_URL=postgresql+asyncpg://opa:opa_password@localhost:5432/quotes
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
```

## Troubleshooting

### Puerto en uso
```bash
# Verificar puertos en uso
netstat -an | grep 5432
netstat -an | grep 6379

# Cambiar puertos en docker-compose.yml si es necesario
```

### Contenedores no inician
```bash
# Ver logs de errores
docker-compose logs postgres
docker-compose logs redis

# Recrear contenedores
docker-compose down -v
docker-compose up -d
```

### Base de datos no inicializa
```bash
# Verificar permisos del script
chmod +x init-db/01-init-timescale.sh

# Ver logs de inicialización
docker-compose logs postgres | grep -A 20 "init-timescale"
```
