"""Circuit breaker middleware for protecting against dependency failures."""

from pybreaker import CircuitBreaker, CircuitBreakerError
from prometheus_client import Counter, Gauge

from opa_quotes_api.config import get_settings
from opa_quotes_api.logging_setup import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Prometheus metrics para circuit breakers
circuit_open_total = Counter(
    "circuit_breaker_open_total",
    "Total circuit breaker opens",
    ["service"]
)

circuit_state = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half-open)",
    ["service"]
)


def on_circuit_open(breaker, *args, **kwargs):
    """
    Callback cuando el circuit breaker se abre.

    Args:
        breaker: CircuitBreaker instance
        *args: Additional arguments
        **kwargs: Additional keyword arguments
    """
    logger.warning(f"Circuit breaker OPENED: {breaker.name}")
    circuit_open_total.labels(service=breaker.name).inc()
    circuit_state.labels(service=breaker.name).set(1)


def on_circuit_close(breaker, *args, **kwargs):
    """
    Callback cuando el circuit breaker se cierra.

    Args:
        breaker: CircuitBreaker instance
        *args: Additional arguments
        **kwargs: Additional keyword arguments
    """
    logger.info(f"Circuit breaker CLOSED: {breaker.name}")
    circuit_state.labels(service=breaker.name).set(0)


def on_circuit_half_open(breaker, *args, **kwargs):
    """
    Callback cuando el circuit breaker pasa a half-open.

    Args:
        breaker: CircuitBreaker instance
        *args: Additional arguments
        **kwargs: Additional keyword arguments
    """
    logger.info(f"Circuit breaker HALF-OPEN: {breaker.name}")
    circuit_state.labels(service=breaker.name).set(2)


# Circuit breaker para Redis
# Configuración desde ENV vars:
# - fail_max: Abrir tras N fallos consecutivos
# - reset_timeout: Mantener abierto N segundos antes de intentar half-open
redis_breaker = CircuitBreaker(
    fail_max=settings.circuit_breaker_redis_fail_max,
    reset_timeout=settings.circuit_breaker_redis_timeout,
    name="redis",
    listeners=[
        (on_circuit_open, "on_open"),
        (on_circuit_close, "on_close"),
        (on_circuit_half_open, "on_half_open"),
    ]
)

# Circuit breaker para TimescaleDB
# Configuración desde ENV vars:
# - fail_max: Más estricto para BD
# - reset_timeout: Mantener abierto N segundos
db_breaker = CircuitBreaker(
    fail_max=settings.circuit_breaker_db_fail_max,
    reset_timeout=settings.circuit_breaker_db_timeout,
    name="timescaledb",
    listeners=[
        (on_circuit_open, "on_open"),
        (on_circuit_close, "on_close"),
        (on_circuit_half_open, "on_half_open"),
    ]
)

# Inicializar métricas en 0 (closed)
circuit_state.labels(service="redis").set(0)
circuit_state.labels(service="timescaledb").set(0)


__all__ = ["redis_breaker", "db_breaker", "CircuitBreakerError"]
