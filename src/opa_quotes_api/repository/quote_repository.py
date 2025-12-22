"""Repository for quotes data access from TimescaleDB."""
from datetime import datetime

from sqlalchemy import desc, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from opa_quotes_api.logging_setup import get_logger
from opa_quotes_api.repository.models import RealTimeQuote
from opa_quotes_api.schemas import OHLCDataPoint, QuoteResponse

logger = get_logger(__name__)


class QuoteRepository:
    """
    Repository for accessing quotes from TimescaleDB.

    Implements data access patterns:
    - Latest quote by ticker
    - Historical OHLC with time_bucket
    - Batch queries for multiple tickers
    """

    def __init__(self, db_session: AsyncSession):
        """Initialize repository with database session."""
        self.db = db_session

    async def get_latest(self, ticker: str) -> QuoteResponse | None:
        """
        Get latest quote for a ticker.

        Args:
            ticker: Stock ticker symbol (uppercase)

        Returns:
            QuoteResponse or None if not found
        """
        try:
            query = (
                select(RealTimeQuote)
                .where(RealTimeQuote.ticker == ticker.upper())
                .order_by(desc(RealTimeQuote.timestamp))
                .limit(1)
            )

            result = await self.db.execute(query)
            quote = result.scalars().first()

            if quote:
                logger.debug(f"Retrieved latest quote for {ticker}")
                return QuoteResponse(
                    ticker=quote.ticker,
                    timestamp=quote.timestamp,
                    open=float(quote.open),
                    high=float(quote.high),
                    low=float(quote.low),
                    close=float(quote.close),
                    volume=int(quote.volume),
                    bid=float(quote.bid) if quote.bid else None,
                    ask=float(quote.ask) if quote.ask else None
                )

            logger.debug(f"No quote found for {ticker}")
            return None

        except Exception as e:
            logger.error(f"Error getting latest quote for {ticker}: {e}")
            return None

    async def get_history(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1m"
    ) -> list[OHLCDataPoint]:
        """
        Get historical OHLC data with time bucketing.

        Args:
            ticker: Stock ticker symbol
            start_date: Start datetime (UTC)
            end_date: End datetime (UTC)
            interval: Aggregation interval (1m, 5m, 15m, 30m, 1h, 1d)

        Returns:
            List of OHLCDataPoint with aggregated OHLC
        """
        try:
            # Map interval to PostgreSQL interval string
            interval_map = {
                "1m": "1 minute",
                "5m": "5 minutes",
                "15m": "15 minutes",
                "30m": "30 minutes",
                "1h": "1 hour",
                "1d": "1 day"
            }

            pg_interval = interval_map.get(interval, "1 minute")

            # Build time_bucket query
            query = text("""
                SELECT
                    time_bucket(:pg_interval, timestamp) AS bucket,
                    FIRST(open, timestamp) AS open,
                    MAX(high) AS high,
                    MIN(low) AS low,
                    LAST(close, timestamp) AS close,
                    SUM(volume) AS volume,
                    LAST(bid, timestamp) AS bid,
                    LAST(ask, timestamp) AS ask
                FROM quotes.real_time
                WHERE ticker = :ticker
                  AND timestamp >= :start_date
                  AND timestamp <= :end_date
                GROUP BY bucket
                ORDER BY bucket ASC
            """)

            result = await self.db.execute(
                query,
                {
                    "pg_interval": pg_interval,
                    "ticker": ticker.upper(),
                    "start_date": start_date,
                    "end_date": end_date
                }
            )

            rows = result.fetchall()

            logger.debug(f"Retrieved {len(rows)} history records for {ticker}")

            quotes = []
            for row in rows:
                quotes.append(OHLCDataPoint(
                    timestamp=row.bucket,
                    open=float(row.open),
                    high=float(row.high),
                    low=float(row.low),
                    close=float(row.close),
                    volume=int(row.volume)
                ))

            return quotes

        except Exception as e:
            logger.error(f"Error getting history for {ticker}: {e}")
            return []

    async def get_batch(self, tickers: list[str]) -> list[QuoteResponse]:
        """
        Get latest quotes for multiple tickers.

        Args:
            tickers: List of ticker symbols

        Returns:
            List of QuoteResponse (only found tickers)
        """
        try:
            # Normalize tickers
            tickers_upper = [t.upper() for t in tickers]

            # Subquery to get latest timestamp per ticker
            latest_subq = (
                select(
                    RealTimeQuote.ticker,
                    func.max(RealTimeQuote.timestamp).label("max_timestamp")
                )
                .where(RealTimeQuote.ticker.in_(tickers_upper))
                .group_by(RealTimeQuote.ticker)
                .subquery()
            )

            # Main query joining with latest timestamps
            query = (
                select(RealTimeQuote)
                .join(
                    latest_subq,
                    (RealTimeQuote.ticker == latest_subq.c.ticker) &
                    (RealTimeQuote.timestamp == latest_subq.c.max_timestamp)
                )
            )

            result = await self.db.execute(query)
            quotes = result.scalars().all()

            logger.debug(f"Retrieved {len(quotes)} quotes from batch of {len(tickers)}")

            return [
                QuoteResponse(
                    ticker=q.ticker,
                    timestamp=q.timestamp,
                    open=float(q.open),
                    high=float(q.high),
                    low=float(q.low),
                    close=float(q.close),
                    volume=int(q.volume),
                    bid=float(q.bid) if q.bid else None,
                    ask=float(q.ask) if q.ask else None
                )
                for q in quotes
            ]

        except Exception as e:
            logger.error(f"Error getting batch quotes: {e}")
            return []

    async def list_tickers(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> list[str]:
        """
        List available tickers.

        Args:
            limit: Maximum number of tickers to return
            offset: Offset for pagination

        Returns:
            List of ticker symbols
        """
        try:
            query = (
                select(RealTimeQuote.ticker)
                .distinct()
                .order_by(RealTimeQuote.ticker)
                .limit(limit)
                .offset(offset)
            )

            result = await self.db.execute(query)
            tickers = [row[0] for row in result.fetchall()]

            logger.debug(f"Listed {len(tickers)} tickers (limit={limit}, offset={offset})")
            return tickers

        except Exception as e:
            logger.error(f"Error listing tickers: {e}")
            return []
