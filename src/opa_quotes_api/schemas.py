"""Pydantic schemas for API requests and responses."""
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class CapacityContext(BaseModel):
    """Capacity scoring context for enrichment."""

    score: float = Field(..., description="Capacity score (0-1)", ge=0, le=1)
    confidence: float = Field(..., description="Model confidence (0-1)", ge=0, le=1)
    last_updated: datetime = Field(..., description="Timestamp of last score update")
    model_version: str = Field(..., description="Model version used for scoring")

    model_config = {
        "json_schema_extra": {
            "example": {
                "score": 0.85,
                "confidence": 0.92,
                "last_updated": "2026-02-10T13:00:00Z",
                "model_version": "1.0.0"
            }
        }
    }


class IntervalEnum(str, Enum):
    """Time interval options for historical data."""

    ONE_MIN = "1m"
    FIVE_MIN = "5m"
    FIFTEEN_MIN = "15m"
    THIRTY_MIN = "30m"
    ONE_HOUR = "1h"
    ONE_DAY = "1d"


class QuoteCreate(BaseModel):
    """Schema para crear una cotización."""

    ticker: str = Field(..., description="Symbol del activo", pattern=r'^[A-Z]{1,10}$')
    timestamp: datetime = Field(..., description="Timestamp de la cotización")
    open: float | None = Field(None, description="Precio de apertura", ge=0)
    high: float | None = Field(None, description="Precio máximo", ge=0)
    low: float | None = Field(None, description="Precio mínimo", ge=0)
    close: float = Field(..., description="Precio de cierre (requerido)", ge=0)
    volume: int | None = Field(None, description="Volumen negociado", ge=0)
    source: str = Field(default="yfinance", description="Fuente de datos", max_length=50)

    model_config = {
        "json_schema_extra": {
            "example": {
                "ticker": "AAPL",
                "timestamp": "2026-01-19T10:30:00Z",
                "open": 150.25,
                "high": 151.00,
                "low": 149.80,
                "close": 150.75,
                "volume": 1500000,
                "source": "yfinance"
            }
        }
    }


class QuoteBatchCreate(BaseModel):
    """Schema para crear múltiples cotizaciones en batch."""

    quotes: list[QuoteCreate] = Field(
        ...,
        description="Lista de cotizaciones a crear",
        min_length=1,
        max_length=1000
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "quotes": [
                    {
                        "ticker": "AAPL",
                        "timestamp": "2026-01-10T09:11:31.294777Z",
                        "price": 259.35,
                        "volume": 318089,
                        "source": "yfinance"
                    }
                ]
            }
        }
    }


class QuoteResponse(BaseModel):
    """Schema de respuesta para cotización individual."""

    ticker: str = Field(..., description="Symbol del activo", min_length=1, max_length=10)
    timestamp: datetime = Field(..., description="Timestamp de la cotización")
    open: Decimal = Field(..., description="Precio de apertura", ge=0)
    high: Decimal = Field(..., description="Precio máximo", ge=0)
    low: Decimal = Field(..., description="Precio mínimo", ge=0)
    close: Decimal = Field(..., description="Precio de cierre", ge=0)
    volume: int = Field(..., description="Volumen negociado", ge=0)
    bid: Decimal | None = Field(None, description="Precio de compra", ge=0)
    ask: Decimal | None = Field(None, description="Precio de venta", ge=0)
    capacity_context: CapacityContext | None = Field(
        None,
        description="Capacity scoring context (optional, when available)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "ticker": "AAPL",
                "timestamp": "2025-12-22T15:30:00Z",
                "open": "150.25",
                "high": "151.10",
                "low": "149.80",
                "close": "150.90",
                "volume": 1000000,
                "bid": "150.85",
                "ask": "150.95"
            }
        }
    }


class HistoryRequest(BaseModel):
    """Schema de request para histórico de cotizaciones."""

    ticker: str = Field(..., description="Symbol del activo", min_length=1, max_length=10)
    start_date: datetime = Field(..., description="Fecha inicio (ISO 8601)")
    end_date: datetime = Field(..., description="Fecha fin (ISO 8601)")
    interval: IntervalEnum = Field(
        default=IntervalEnum.ONE_MIN,
        description="Intervalo de agregación"
    )

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: datetime, info) -> datetime:
        """Validate that end_date is after start_date."""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "ticker": "AAPL",
                "start_date": "2025-12-22T09:30:00Z",
                "end_date": "2025-12-22T16:00:00Z",
                "interval": "5m"
            }
        }
    }


class OHLCDataPoint(BaseModel):
    """OHLC data point para histórico."""

    timestamp: datetime = Field(..., description="Timestamp del intervalo")
    open: Decimal = Field(..., description="Precio de apertura", ge=0)
    high: Decimal = Field(..., description="Precio máximo", ge=0)
    low: Decimal = Field(..., description="Precio mínimo", ge=0)
    close: Decimal = Field(..., description="Precio de cierre", ge=0)
    volume: int = Field(..., description="Volumen total", ge=0)


class HistoryResponse(BaseModel):
    """Schema de respuesta para histórico de cotizaciones."""

    ticker: str = Field(..., description="Symbol del activo")
    interval: IntervalEnum = Field(..., description="Intervalo usado")
    data: list[OHLCDataPoint] = Field(..., description="Serie temporal OHLC")
    count: int = Field(..., description="Cantidad de puntos de datos", ge=0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "ticker": "AAPL",
                "interval": "5m",
                "data": [
                    {
                        "timestamp": "2025-12-22T09:30:00Z",
                        "open": "150.00",
                        "high": "150.50",
                        "low": "149.80",
                        "close": "150.25",
                        "volume": 50000
                    },
                    {
                        "timestamp": "2025-12-22T09:35:00Z",
                        "open": "150.25",
                        "high": "150.75",
                        "low": "150.10",
                        "close": "150.50",
                        "volume": 45000
                    }
                ],
                "count": 2
            }
        }
    }


class BatchRequest(BaseModel):
    """Schema de request para batch de cotizaciones."""

    tickers: list[str] = Field(
        ...,
        description="Lista de symbols",
        min_length=1,
        max_length=50
    )

    @field_validator('tickers')
    @classmethod
    def validate_tickers(cls, v: list[str]) -> list[str]:
        """Validate and normalize ticker list."""
        # Remove duplicates and convert to uppercase
        normalized = list(set(ticker.upper().strip() for ticker in v))
        if not normalized:
            raise ValueError('tickers list cannot be empty after normalization')
        return normalized

    model_config = {
        "json_schema_extra": {
            "example": {
                "tickers": ["AAPL", "GOOGL", "MSFT", "AMZN"]
            }
        }
    }


class BatchQuoteItem(BaseModel):
    """Item individual en respuesta batch."""

    ticker: str = Field(..., description="Symbol del activo")
    quote: QuoteResponse | None = Field(None, description="Cotización (null si no existe)")
    error: str | None = Field(None, description="Mensaje de error si falla")


class QuoteBatchResponse(BaseModel):
    """Schema de respuesta para creación batch según OPA-269."""

    status: str = Field(..., description="Estado: success, partial o error")
    created: int = Field(..., description="Cantidad de quotes creados", ge=0)
    failed: int = Field(default=0, description="Cantidad de quotes fallidos", ge=0)
    errors: list[dict] | None = Field(None, description="Lista de errores (si failed > 0)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "success",
                    "created": 10,
                    "failed": 0
                },
                {
                    "status": "partial",
                    "created": 8,
                    "failed": 2,
                    "errors": [
                        {"ticker": "INVALID", "reason": "Ticker format invalid"}
                    ]
                }
            ]
        }
    }


class BatchResponse(BaseModel):
    """Schema de respuesta para batch de cotizaciones (GET)."""

    quotes: list[BatchQuoteItem] = Field(..., description="Lista de cotizaciones")
    total: int = Field(..., description="Total de items solicitados", ge=0)
    successful: int = Field(..., description="Items exitosos", ge=0)
    failed: int = Field(..., description="Items fallidos", ge=0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "quotes": [
                    {
                        "ticker": "AAPL",
                        "quote": {
                            "ticker": "AAPL",
                            "timestamp": "2025-12-22T15:30:00Z",
                            "open": "150.25",
                            "high": "151.10",
                            "low": "149.80",
                            "close": "150.90",
                            "volume": 1000000,
                            "bid": "150.85",
                            "ask": "150.95"
                        },
                        "error": None
                    },
                    {
                        "ticker": "INVALID",
                        "quote": None,
                        "error": "Ticker not found"
                    }
                ],
                "total": 2,
                "successful": 1,
                "failed": 1
            }
        }
    }


class ErrorResponse(BaseModel):
    """Schema de respuesta para errores."""

    detail: str = Field(..., description="Mensaje de error")
    error_code: str | None = Field(None, description="Código de error interno")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp del error")

    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": "Ticker not found",
                "error_code": "TICKER_NOT_FOUND",
                "timestamp": "2025-12-22T15:30:00Z"
            }
        }
    }


class HealthResponse(BaseModel):
    """Schema de respuesta para health check."""

    status: str = Field(..., description="Estado del servicio")
    version: str = Field(..., description="Versión de la API")
    repository: str = Field(..., description="Nombre del repositorio")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de respuesta")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "ok",
                "version": "0.1.0",
                "repository": "opa-quotes-api",
                "timestamp": "2025-12-22T15:30:00Z"
            }
        }
    }
