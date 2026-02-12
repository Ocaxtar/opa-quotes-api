"""
opa-quotes-api - FastAPI application
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from prometheus_fastapi_instrumentator import Instrumentator

from opa_quotes_api.config import get_settings
from opa_quotes_api.database import engine
from opa_quotes_api.logging_setup import setup_logging
from opa_quotes_api.routers import quotes, websocket
from opa_quotes_api.services.capacity_subscriber import CapacitySubscriber

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Settings
settings = get_settings()

# Global subscriber instance
_capacity_subscriber: CapacitySubscriber | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global _capacity_subscriber
    
    logger.info(f"Starting {settings.app_name} v{settings.version}")

    # Startup: Initialize capacity subscriber
    try:
        _capacity_subscriber = CapacitySubscriber()
        await _capacity_subscriber.connect()
        # Start listening in background task
        asyncio.create_task(_capacity_subscriber.listen())
        logger.info("Capacity subscriber started")
    except Exception as e:
        logger.warning(f"Could not start capacity subscriber: {e}")
        # Continue without subscriber (graceful degradation)

    yield

    # Shutdown
    logger.info("Shutting down...")
    if _capacity_subscriber:
        await _capacity_subscriber.disconnect()
        logger.info("Capacity subscriber stopped")
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.effective_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"],
    max_age=3600,  # Cache preflight por 1 hora
)

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Instrumentar FastAPI con métricas HTTP (requests, latencia, etc.)
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": settings.version,
        "repository": "opa-quotes-api",
    }


# Include routers with /v1 prefix
app.include_router(quotes.router, prefix="/v1")
app.include_router(websocket.router, prefix="/v1")

# OPA-506: Include websocket router without version prefix for compatibility
# Allows connections to ws://localhost:8000/ws/quotes (in addition to /v1/ws/quotes)
app.include_router(websocket.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "opa_quotes_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
