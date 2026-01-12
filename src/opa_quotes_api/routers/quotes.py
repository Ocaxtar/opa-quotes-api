"""FastAPI router for quote endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from opa_quotes_api.dependencies import get_quote_service
from opa_quotes_api.schemas import (
    BatchRequest,
    BatchResponse,
    HistoryRequest,
    HistoryResponse,
    QuoteBatchCreate,
    QuoteResponse,
)
from opa_quotes_api.services.quote_service import QuoteService

router = APIRouter(
    prefix="/quotes",
    tags=["quotes"],
    responses={
        404: {"description": "Quote not found"},
        500: {"description": "Internal server error"},
    },
)


@router.get(
    "/{ticker}/latest",
    response_model=QuoteResponse,
    summary="Get latest quote",
    description="Retrieve the most recent quote for a given ticker symbol",
)
async def get_latest_quote(
    ticker: str = Path(..., description="Ticker symbol (e.g., AAPL)", min_length=1, max_length=10),
    service: QuoteService = Depends(get_quote_service)
) -> QuoteResponse:
    """
    Get the latest quote for a ticker.

    Args:
        ticker: Stock ticker symbol
        service: Injected QuoteService

    Returns:
        QuoteResponse with the latest market data

    Raises:
        HTTPException: 404 if ticker not found
    """
    quote = await service.get_latest(ticker)

    if not quote:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker {ticker} not found"
        )

    return quote


@router.post(
    "/{ticker}/history",
    response_model=HistoryResponse,
    summary="Get historical quotes",
    description="Retrieve historical OHLC data for a ticker within a date range",
)
async def get_history(
    ticker: str = Path(..., description="Ticker symbol (e.g., AAPL)", min_length=1, max_length=10),
    request: HistoryRequest = None,
    service: QuoteService = Depends(get_quote_service)
) -> HistoryResponse:
    """
    Get historical quotes for a ticker.

    Args:
        ticker: Stock ticker symbol
        request: History request with date range and interval
        service: Injected QuoteService

    Returns:
        HistoryResponse with OHLC time series data

    Raises:
        HTTPException: 404 if ticker not found
        HTTPException: 400 if date range invalid
    """
    # Validate ticker matches request
    if request.ticker != ticker:
        raise HTTPException(
            status_code=400,
            detail="Ticker in URL must match ticker in request body"
        )

    response = await service.get_history(request)
    return response


@router.get(
    "/batch",
    response_model=BatchResponse,
    summary="Get multiple quotes",
    description="Retrieve latest quotes for multiple tickers in a single request",
)
async def get_batch_quotes(
    request: BatchRequest,
    service: QuoteService = Depends(get_quote_service)
) -> BatchResponse:
    """
    Get quotes for multiple tickers.

    Args:
        request: Batch request with list of ticker symbols
        service: Injected QuoteService

    Returns:
        BatchResponse with quotes for each ticker
    """
    response = await service.get_batch(request)
    return response


@router.post(
    "/batch",
    status_code=201,
    summary="Create multiple quotes",
    description="Create multiple quotes in a single batch request (for storage publisher)",
)
async def create_quotes_batch(
    batch: QuoteBatchCreate,
    service: QuoteService = Depends(get_quote_service)
) -> dict:
    """
    Create quotes in batch.

    Args:
        batch: Batch of quotes to create
        service: Injected QuoteService

    Returns:
        dict with created count
    """
    result = await service.create_batch(batch.quotes)
    return result


@router.get(
    "/",
    response_model=list[str],
    summary="List available tickers",
    description="Get a list of all available ticker symbols",
)
async def list_tickers(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tickers to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    service: QuoteService = Depends(get_quote_service)
) -> list[str]:
    """
    List available tickers with pagination.

    Args:
        limit: Maximum number of tickers to return
        offset: Pagination offset
        service: Injected QuoteService

    Returns:
        List of ticker symbols
    """
    tickers = await service.list_tickers(limit, offset)
    return tickers
