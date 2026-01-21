"""Rate limiting middleware using slowapi."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from opa_quotes_api.config import get_settings

settings = get_settings()

# Inicializar limiter con Redis storage
# Redis persiste los límites, sobreviviendo restarts de la API
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url,
    strategy="fixed-window",  # Fixed window strategy
)


def get_rate_limit_for_tier(api_key: str | None) -> str:
    """
    Determina el rate limit según el tier del usuario.

    Args:
        api_key: API key del usuario (None = free tier)

    Returns:
        String de rate limit (ej: "100/minute")

    Nota:
        En producción, esto consultaría una BD o servicio de autenticación.
        Por ahora, implementamos lógica simple basada en presencia de API key.
    """
    # TODO (OPA-306): Integrar con servicio de autenticación real
    if api_key is None:
        return "100/minute"  # Free tier
    elif api_key.startswith("pro_"):
        return "1000/minute"  # Pro tier
    elif api_key.startswith("enterprise_"):
        return "10000/minute"  # Enterprise tier
    else:
        return "100/minute"  # Default free tier


__all__ = ["limiter", "get_rate_limit_for_tier"]
