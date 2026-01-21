"""FastAPI router for quote endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

from opa_quotes_api.dependencies import get_quote_service
from opa_quotes_api.middleware.circuit_breaker import CircuitBreakerError
from opa_quotes_api.middleware.rate_limit import limiter
from opa_quotes_api.schemas import (
    BatchRequest,
    BatchResponse,
    HistoryRequest,
    HistoryResponse,
    QuoteBatchCreate,
    QuoteBatchResponse,
    QuoteResponse,
)
from opa_quotes_api.services.quote_service import QuoteService

router = APIRouter(
    prefix="/quotes",
    tags=["quotes"],
    responses={
        404: {"description": "Quote not found"},
        500: {"description": "Internal server error"},
        503: {"description": "Service unavailable (dependencies down)"},
    },
)


@router.get(
    "/{ticker}/latest",
    response_model=QuoteResponse,
    summary="Get latest quote",
    description="Retrieve the most recent quote for a given ticker symbol",
)
@limiter.limit("100/minute")  # Rate limit: 100 requests/minuto
async def get_latest_quote(
    ticker: str,
    request: Request,
    service: QuoteService = Depends(get_quote_service)
) -> QuoteResponse:
    """
    Get the latest quote for a ticker.

    Args:
        request: FastAPI Request object (para rate limiting)
        ticker: Stock ticker symbol
        service: Injected QuoteService

    Returns:
        QuoteResponse with the latest market data

    Raises:
        HTTPException: 404 if ticker not found
        HTTPException: 503 if service unavailable (circuit breaker open)
    """
    try:
        quote = await service.get_latest(ticker)

        if not quote:
            raise HTTPException(
                status_code=404,
                detail=f"Ticker {ticker} not found"
            )

        return quote
    except CircuitBreakerError:
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable (dependencies down)"
        )


@router.post(
    "/{ticker}/history",
    response_model=HistoryResponse,
    summary="Get historical quotes",
    description="Retrieve historical OHLC data for a ticker within a date range",
)
@limiter.limit("20/minute")  # Más restrictivo para queries pesadas
async def get_history(
    ticker: str,
    request: Request,
    history_request: HistoryRequest,
    service: QuoteService = Depends(get_quote_service)
) -> HistoryResponse:
    """
    Get historical quotes for a ticker.

    Args:
        request: FastAPI Request object (para rate limiting)
        ticker: Stock ticker symbol
        history_request: History request with date range and interval
        service: Injected QuoteService

    Returns:
        HistoryResponse with OHLC time series data

    Raises:
        HTTPException: 404 if ticker not found
        HTTPException: 400 if date range invalid
        HTTPException: 503 if service unavailable (circuit breaker open)
    """
    # Validate ticker matches request
    if history_request.ticker != ticker:
        raise HTTPException(
            status_code=400,
            detail="Ticker in URL must match ticker in request body"
        )

    try:
        response = await service.get_history(history_request)
        return response
    except CircuitBreakerError:
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable (dependencies down)"
        )


@router.post(
    "/batch",
    status_code=201,
    response_model=QuoteBatchResponse,
    summary="Create multiple quotes",
    description="Create multiple quotes in a single batch request (for storage publisher)",
)
@limiter.limit("50/minute")  # Rate limit para batch creation
async def create_quotes_batch(
    request: Request,
    batch: QuoteBatchCreate,
    service: QuoteService = Depends(get_quote_service)
) -> QuoteBatchResponse:
    """
    Create quotes in batch (OPA-269).

    Args:
        request: FastAPI Request object (para rate limiting)
        batch: Batch of quotes to create
        service: Injected QuoteService

    Returns:
        QuoteBatchResponse with created/failed counts

    Raises:
        HTTPException: 503 if database unavailable
    """
    try:
        result = await service.create_batch(batch.quotes)
        
        return QuoteBatchResponse(
            status=result["status"],
            created=result["created"],
            failed=result["failed"],
            errors=result.get("errors")
        )
    except CircuitBreakerError:
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable (dependencies down)"
        )


@router.get(
    "/batch",
    response_model=BatchResponse,
    summary="Get multiple quotes",
    description="Retrieve latest quotes for multiple tickers in a single request",
)
@limiter.limit("50/minute")  # Rate limit para batch queries
async def get_batch_quotes(
    request: Request,
    batch_request: BatchRequest,
    service: QuoteService = Depends(get_quote_service)
) -> BatchResponse:
    """
    Get quotes for multiple tickers.

    Args:
        request: FastAPI Request object (para rate limiting) y BatchRequest
        batch_request: Batch request with list of ticker symbols
        service: Injected QuoteService

    Returns:
        BatchResponse with quotes for each ticker

    Raises:
        HTTPException: 503 if service unavailable (circuit breaker open)
    """
    try:
        response = await service.get_batch(batch_request)
        return response
    except CircuitBreakerError:
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable (dependencies down)"
        )


@router.get(
    "/",
    response_model=list[str],
    summary="List available tickers",
    description="Get a list of all available ticker symbols",
)
@limiter.limit("30/minute")  # Rate limit para listado
async def list_tickers(
    request: Request,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tickers to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    service: QuoteService = Depends(get_quote_service)
) -> list[str]:
    """
    List available tickers with pagination.

    Args:
        request: FastAPI Request object (para rate limiting)
        limit: Maximum number of tickers to return
        offset: Pagination offset
        service: Injected QuoteService

    Returns:
        List of ticker symbols

    Raises:
        HTTPException: 503 if service unavailable (circuit breaker open)
    """
    try:
        tickers = await service.list_tickers(limit, offset)
        return tickers
    except CircuitBreakerError:
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable (dependencies down)"
        )
