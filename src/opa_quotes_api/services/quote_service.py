"""Quote service with business logic and caching."""
import json

from opa_quotes_api.logging_setup import get_logger
from opa_quotes_api.repository.quote_repository import QuoteRepository
from opa_quotes_api.schemas import (
    BatchQuoteItem,
    BatchRequest,
    BatchResponse,
    CapacityContext,
    HistoryRequest,
    HistoryResponse,
    QuoteResponse,
)
from opa_quotes_api.services.cache_service import CacheService

logger = get_logger(__name__)


class QuoteService:
    """
    Service layer for quote operations.

    Implements business logic:
    - Cache-first strategy for latest quotes
    - History queries with cache
    - Batch processing
    """

    def __init__(
        self,
        cache: CacheService,
        repository: QuoteRepository
    ):
        """Initialize service with cache and repository."""
        self.cache = cache
        self.repository = repository

    async def get_latest(self, ticker: str) -> QuoteResponse | None:
        """
        Get latest quote with cache-first strategy.

        Args:
            ticker: Stock ticker symbol

        Returns:
            QuoteResponse or None if not found
        """
        ticker = ticker.upper()

        # Try cache first
        cache_key = self.cache.make_latest_key(ticker)
        cached = await self.cache.get(cache_key)

        if cached:
            try:
                quote = QuoteResponse.model_validate_json(cached)
                # Enrich with capacity context (graceful degradation)
                await self._enrich_with_capacity(quote)
                return quote
            except Exception as e:
                logger.warning(f"Failed to deserialize cached quote for {ticker}: {e}")

        # Cache miss - query database
        quote = await self.repository.get_latest(ticker)

        if quote:
            # Enrich with capacity context before caching
            await self._enrich_with_capacity(quote)
            
            # Cache result
            await self.cache.set(
                cache_key,
                quote.model_dump_json(),
                ttl=self.cache.default_ttl
            )

        return quote

    async def get_history(
        self,
        request: HistoryRequest
    ) -> HistoryResponse:
        """
        Get historical quotes with optional caching.

        Args:
            request: History request with date range and interval

        Returns:
            HistoryResponse with time series data
        """
        ticker = request.ticker.upper()

        # Generate cache key
        cache_key = self.cache.make_history_key(
            ticker,
            request.start_date.isoformat(),
            request.end_date.isoformat(),
            request.interval.value
        )

        # Try cache
        cached = await self.cache.get(cache_key)
        if cached:
            try:
                return HistoryResponse.model_validate_json(cached)
            except Exception as e:
                logger.warning(f"Failed to deserialize cached history for {ticker}: {e}")

        # Query database
        data_points = await self.repository.get_history(
            ticker,
            request.start_date,
            request.end_date,
            request.interval.value
        )

        response = HistoryResponse(
            ticker=ticker,
            interval=request.interval,
            data=data_points,
            count=len(data_points)
        )

        # Cache result (longer TTL for history)
        await self.cache.set(
            cache_key,
            response.model_dump_json(),
            ttl=self.cache.history_ttl
        )

        return response

    async def get_batch(
        self,
        request: BatchRequest
    ) -> BatchResponse:
        """
        Get multiple quotes in batch.

        Args:
            request: Batch request with list of tickers

        Returns:
            BatchResponse with found quotes and not found tickers
        """
        # Normalize tickers
        tickers = [t.upper() for t in request.tickers]

        # Query all tickers from database
        found_quotes = await self.repository.get_batch(tickers)

        # Determine which tickers were not found
        found_tickers = {q.ticker for q in found_quotes}

        # Build batch response
        batch_items = []
        successful = 0
        failed = 0

        for ticker in tickers:
            if ticker in found_tickers:
                quote = next(q for q in found_quotes if q.ticker == ticker)
                
                # Enrich with capacity context
                await self._enrich_with_capacity(quote)
                
                batch_items.append(BatchQuoteItem(
                    ticker=ticker,
                    quote=quote,
                    error=None
                ))
                successful += 1

                # Cache individual quote
                cache_key = self.cache.make_latest_key(ticker)
                await self.cache.set(
                    cache_key,
                    quote.model_dump_json(),
                    ttl=self.cache.default_ttl
                )
            else:
                batch_items.append(BatchQuoteItem(
                    ticker=ticker,
                    quote=None,
                    error="Ticker not found"
                ))
                failed += 1

        return BatchResponse(
            quotes=batch_items,
            total=len(tickers),
            successful=successful,
            failed=failed
        )

    async def create_batch(self, quotes: list) -> dict:
        """
        Create multiple quotes in batch.

        Args:
            quotes: List of QuoteCreate objects

        Returns:
            dict with status, created, failed, and errors
        """
        result = await self.repository.create_batch(quotes)
        logger.info(f"Batch operation: {result['status']} - {result['created']} created, {result['failed']} failed")
        return result

    async def list_tickers(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> list[str]:
        """
        List available tickers.

        Args:
            limit: Maximum number to return
            offset: Offset for pagination

        Returns:
            List of ticker symbols
        """
        return await self.repository.list_tickers(limit, offset)

    async def _enrich_with_capacity(self, quote: QuoteResponse) -> None:
        """
        Enrich quote with capacity context if available.
        
        Implements graceful degradation: fails silently if Redis unavailable
        or capacity score not cached.
        
        Args:
            quote: QuoteResponse to enrich (modified in-place)
        """
        try:
            capacity_key = f"capacity:score:{quote.ticker}"
            capacity_data = await self.cache.get(capacity_key)
            
            if capacity_data:
                capacity_dict = json.loads(capacity_data)
                quote.capacity_context = CapacityContext(**capacity_dict)
                logger.debug(f"Enriched {quote.ticker} with capacity context")
        except Exception as e:
            # Graceful degradation: log but don't fail the request
            logger.debug(f"Could not enrich {quote.ticker} with capacity: {e}")
