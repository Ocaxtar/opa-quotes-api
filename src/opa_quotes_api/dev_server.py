"""Development server startup script."""
import uvicorn

from opa_quotes_api.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "opa_quotes_api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
