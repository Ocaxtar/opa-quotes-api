"""Logging configuration for opa-quotes-api."""
import logging
import sys

from opa_quotes_api.config import get_settings


def setup_logging() -> None:
    """Configure logging for the application."""
    settings = get_settings()

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Module name (__name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
