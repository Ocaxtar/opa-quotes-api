"""Unit tests for Pydantic schemas."""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from opa_quotes_api.schemas import (
    BatchRequest,
    BatchResponse,
    ErrorResponse,
    HealthResponse,
    HistoryRequest,
    HistoryResponse,
    IntervalEnum,
    OHLCDataPoint,
    QuoteResponse,
)


class TestQuoteResponse:
    """Tests for QuoteResponse schema."""
    
    def test_valid_quote(self):
        """Test valid quote creation."""
        quote = QuoteResponse(
            ticker="AAPL",
            timestamp=datetime(2025, 12, 22, 15, 30, 0),
            open=Decimal("150.25"),
            high=Decimal("151.10"),
            low=Decimal("149.80"),
            close=Decimal("150.90"),
            volume=1000000,
            bid=Decimal("150.85"),
            ask=Decimal("150.95")
        )
        
        assert quote.ticker == "AAPL"
        assert quote.open == Decimal("150.25")
        assert quote.volume == 1000000
    
    def test_quote_without_bid_ask(self):
        """Test quote without optional bid/ask."""
        quote = QuoteResponse(
            ticker="AAPL",
            timestamp=datetime(2025, 12, 22, 15, 30, 0),
            open=Decimal("150.25"),
            high=Decimal("151.10"),
            low=Decimal("149.80"),
            close=Decimal("150.90"),
            volume=1000000
        )
        
        assert quote.bid is None
        assert quote.ask is None
    
    def test_negative_price_validation(self):
        """Test that negative prices are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            QuoteResponse(
                ticker="AAPL",
                timestamp=datetime(2025, 12, 22, 15, 30, 0),
                open=Decimal("-150.25"),
                high=Decimal("151.10"),
                low=Decimal("149.80"),
                close=Decimal("150.90"),
                volume=1000000
            )
        
        assert "greater than or equal to 0" in str(exc_info.value)
    
    def test_negative_volume_validation(self):
        """Test that negative volume is rejected."""
        with pytest.raises(ValidationError):
            QuoteResponse(
                ticker="AAPL",
                timestamp=datetime(2025, 12, 22, 15, 30, 0),
                open=Decimal("150.25"),
                high=Decimal("151.10"),
                low=Decimal("149.80"),
                close=Decimal("150.90"),
                volume=-1000000
            )
    
    def test_json_serialization(self):
        """Test JSON serialization."""
        quote = QuoteResponse(
            ticker="AAPL",
            timestamp=datetime(2025, 12, 22, 15, 30, 0),
            open=Decimal("150.25"),
            high=Decimal("151.10"),
            low=Decimal("149.80"),
            close=Decimal("150.90"),
            volume=1000000
        )
        
        json_data = quote.model_dump_json()
        assert "AAPL" in json_data
        assert "150.25" in json_data


class TestHistoryRequest:
    """Tests for HistoryRequest schema."""
    
    def test_valid_history_request(self):
        """Test valid history request."""
        start = datetime(2025, 12, 22, 9, 30, 0)
        end = datetime(2025, 12, 22, 16, 0, 0)
        
        request = HistoryRequest(
            ticker="AAPL",
            start_date=start,
            end_date=end,
            interval=IntervalEnum.FIVE_MIN
        )
        
        assert request.ticker == "AAPL"
        assert request.interval == IntervalEnum.FIVE_MIN
    
    def test_end_before_start_validation(self):
        """Test that end_date before start_date is rejected."""
        start = datetime(2025, 12, 22, 16, 0, 0)
        end = datetime(2025, 12, 22, 9, 30, 0)
        
        with pytest.raises(ValidationError) as exc_info:
            HistoryRequest(
                ticker="AAPL",
                start_date=start,
                end_date=end,
                interval=IntervalEnum.FIVE_MIN
            )
        
        assert "after start_date" in str(exc_info.value)
    
    def test_default_interval(self):
        """Test default interval is 1m."""
        start = datetime(2025, 12, 22, 9, 30, 0)
        end = datetime(2025, 12, 22, 16, 0, 0)
        
        request = HistoryRequest(
            ticker="AAPL",
            start_date=start,
            end_date=end
        )
        
        assert request.interval == IntervalEnum.ONE_MIN


class TestBatchRequest:
    """Tests for BatchRequest schema."""
    
    def test_valid_batch_request(self):
        """Test valid batch request."""
        request = BatchRequest(tickers=["AAPL", "GOOGL", "MSFT"])
        
        assert len(request.tickers) == 3
        assert "AAPL" in request.tickers
    
    def test_ticker_normalization(self):
        """Test that tickers are normalized (uppercase, no duplicates)."""
        request = BatchRequest(tickers=["aapl", "AAPL", " googl ", "MSFT"])
        
        assert len(request.tickers) == 3  # Duplicates removed
        assert all(t == t.upper() for t in request.tickers)
        assert all(t == t.strip() for t in request.tickers)
    
    def test_empty_ticker_list(self):
        """Test that empty ticker list is rejected."""
        with pytest.raises(ValidationError):
            BatchRequest(tickers=[])
    
    def test_max_tickers_validation(self):
        """Test max 50 tickers validation."""
        with pytest.raises(ValidationError):
            BatchRequest(tickers=[f"TICK{i}" for i in range(51)])


class TestHistoryResponse:
    """Tests for HistoryResponse schema."""
    
    def test_valid_history_response(self):
        """Test valid history response."""
        data_points = [
            OHLCDataPoint(
                timestamp=datetime(2025, 12, 22, 9, 30, 0),
                open=Decimal("150.00"),
                high=Decimal("150.50"),
                low=Decimal("149.80"),
                close=Decimal("150.25"),
                volume=50000
            ),
            OHLCDataPoint(
                timestamp=datetime(2025, 12, 22, 9, 35, 0),
                open=Decimal("150.25"),
                high=Decimal("150.75"),
                low=Decimal("150.10"),
                close=Decimal("150.50"),
                volume=45000
            )
        ]
        
        response = HistoryResponse(
            ticker="AAPL",
            interval=IntervalEnum.FIVE_MIN,
            data=data_points,
            count=2
        )
        
        assert response.ticker == "AAPL"
        assert response.count == 2
        assert len(response.data) == 2


class TestBatchResponse:
    """Tests for BatchResponse schema."""
    
    def test_valid_batch_response(self):
        """Test valid batch response."""
        quote = QuoteResponse(
            ticker="AAPL",
            timestamp=datetime(2025, 12, 22, 15, 30, 0),
            open=Decimal("150.25"),
            high=Decimal("151.10"),
            low=Decimal("149.80"),
            close=Decimal("150.90"),
            volume=1000000
        )
        
        response = BatchResponse(
            quotes=[
                {"ticker": "AAPL", "quote": quote, "error": None},
                {"ticker": "INVALID", "quote": None, "error": "Ticker not found"}
            ],
            total=2,
            successful=1,
            failed=1
        )
        
        assert response.total == 2
        assert response.successful == 1
        assert response.failed == 1


class TestErrorResponse:
    """Tests for ErrorResponse schema."""
    
    def test_error_response(self):
        """Test error response."""
        error = ErrorResponse(
            detail="Ticker not found",
            error_code="TICKER_NOT_FOUND"
        )
        
        assert error.detail == "Ticker not found"
        assert error.error_code == "TICKER_NOT_FOUND"
        assert isinstance(error.timestamp, datetime)


class TestHealthResponse:
    """Tests for HealthResponse schema."""
    
    def test_health_response(self):
        """Test health response."""
        health = HealthResponse(
            status="ok",
            version="0.1.0",
            repository="opa-quotes-api"
        )
        
        assert health.status == "ok"
        assert health.version == "0.1.0"
        assert isinstance(health.timestamp, datetime)


class TestIntervalEnum:
    """Tests for IntervalEnum."""
    
    def test_all_intervals(self):
        """Test all interval values."""
        assert IntervalEnum.ONE_MIN.value == "1m"
        assert IntervalEnum.FIVE_MIN.value == "5m"
        assert IntervalEnum.FIFTEEN_MIN.value == "15m"
        assert IntervalEnum.THIRTY_MIN.value == "30m"
        assert IntervalEnum.ONE_HOUR.value == "1h"
        assert IntervalEnum.ONE_DAY.value == "1d"
