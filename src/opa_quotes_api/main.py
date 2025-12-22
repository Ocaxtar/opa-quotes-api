"""
opa-quotes-api - FastAPI application
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from opa_quotes_api.config import get_settings
from opa_quotes_api.database import engine
from opa_quotes_api.logging_setup import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    logger.info(f"Starting {settings.app_name} v{settings.version}")
    
    # Startup
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": settings.version,
        "repository": "opa-quotes-api",
    }


# Import routers
# from opa_quotes_api.routers import example_router
# app.include_router(example_router.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
