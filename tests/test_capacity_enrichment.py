"""Tests for capacity enrichment integration."""
import json
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opa_quotes_api.schemas import CapacityContext, QuoteResponse
from opa_quotes_api.services.capacity_subscriber import CapacitySubscriber
from opa_quotes_api.services.quote_service import QuoteService


@pytest.fixture
def mock_cache_service():
    """Mock cache service for testing."""
    cache = MagicMock()
    cache.get = AsyncMock()
    cache.set = AsyncMock()
    cache.default_ttl = 5
    cache.history_ttl = 60
    cache.make_latest_key = lambda ticker: f"quote:latest:{ticker}"
    return cache


@pytest.fixture
def mock_repository():
    """Mock repository for testing."""
    repo = MagicMock()
    repo.get_latest = AsyncMock()
    repo.get_batch = AsyncMock()
    return repo


@pytest.fixture
def sample_quote():
    """Sample quote response without capacity context."""
    return QuoteResponse(
        ticker="AAPL",
        timestamp=datetime(2026, 2, 10, 13, 0, 0),
        open=Decimal("150.25"),
        high=Decimal("151.10"),
        low=Decimal("149.80"),
        close=Decimal("150.90"),
        volume=1000000,
        bid=Decimal("150.85"),
        ask=Decimal("150.95"),
        capacity_context=None
    )


@pytest.fixture
def sample_capacity_context():
    """Sample capacity context data."""
    return {
        "score": 0.85,
        "confidence": 0.92,
        "last_updated": "2026-02-10T13:00:00Z",
        "model_version": "1.0.0"
    }


class TestCapacityEnrichment:
    """Tests for capacity context enrichment in quotes."""

    @pytest.mark.asyncio
    async def test_enrichment_with_score_available(
        self, mock_cache_service, mock_repository, sample_quote, sample_capacity_context
    ):
        """Quote response includes capacity_context when score available in Redis."""
        # Arrange
        mock_repository.get_latest.return_value = sample_quote
        mock_cache_service.get.side_effect = [
            None,  # First call: quote cache miss
            json.dumps(sample_capacity_context)  # Second call: capacity score hit
        ]

        service = QuoteService(mock_cache_service, mock_repository)

        # Act
        result = await service.get_latest("AAPL")

        # Assert
        assert result is not None
        assert result.ticker == "AAPL"
        assert result.capacity_context is not None
        assert result.capacity_context.score == 0.85
        assert result.capacity_context.confidence == 0.92
        assert result.capacity_context.model_version == "1.0.0"

    @pytest.mark.asyncio
    async def test_enrichment_without_score(
        self, mock_cache_service, mock_repository, sample_quote
    ):
        """Quote response works without capacity_context (graceful degradation)."""
        # Arrange
        mock_repository.get_latest.return_value = sample_quote
        mock_cache_service.get.return_value = None  # Both caches miss

        service = QuoteService(mock_cache_service, mock_repository)

        # Act
        result = await service.get_latest("AAPL")

        # Assert
        assert result is not None
        assert result.ticker == "AAPL"
        assert result.capacity_context is None  # No enrichment

    @pytest.mark.asyncio
    async def test_enrichment_with_invalid_json(
        self, mock_cache_service, mock_repository, sample_quote
    ):
        """Graceful degradation when capacity data is invalid JSON."""
        # Arrange
        mock_repository.get_latest.return_value = sample_quote
        mock_cache_service.get.side_effect = [
            None,  # Quote cache miss
            "invalid json data"  # Invalid capacity data
        ]

        service = QuoteService(mock_cache_service, mock_repository)

        # Act
        result = await service.get_latest("AAPL")

        # Assert
        assert result is not None
        assert result.ticker == "AAPL"
        assert result.capacity_context is None  # Failed gracefully

    @pytest.mark.asyncio
    async def test_enrichment_redis_exception(
        self, mock_cache_service, mock_repository, sample_quote
    ):
        """Graceful degradation when Redis raises exception."""
        # Arrange
        mock_repository.get_latest.return_value = sample_quote
        mock_cache_service.get.side_effect = [
            None,  # Quote cache miss
            Exception("Redis connection failed")  # Redis error
        ]

        service = QuoteService(mock_cache_service, mock_repository)

        # Act
        result = await service.get_latest("AAPL")

        # Assert
        assert result is not None
        assert result.ticker == "AAPL"
        assert result.capacity_context is None  # Failed gracefully


class TestCapacitySubscriber:
    """Tests for CapacitySubscriber service."""

    @pytest.mark.asyncio
    async def test_subscriber_caches_with_correct_ttl(self):
        """Verify cached scores have 1-hour TTL."""
        # Arrange
        subscriber = CapacitySubscriber("redis://localhost:6379/0")
        subscriber.redis = AsyncMock()

        message = {
            "type": "message",
            "data": json.dumps({
                "ticker": "AAPL",
                "score": 0.85,
                "confidence": 0.92,
                "timestamp": "2026-02-10T13:00:00Z",
                "model_version": "1.0.0"
            })
        }

        # Act
        await subscriber._process_message(message)

        # Assert
        subscriber.redis.setex.assert_called_once()
        call_args = subscriber.redis.setex.call_args
        assert call_args[0][0] == "capacity:score:AAPL"  # Key
        assert call_args[0][1] == 3600  # TTL (1 hour)

        # Verify cached payload structure
        cached_data = json.loads(call_args[0][2])
        assert cached_data["score"] == 0.85
        assert cached_data["confidence"] == 0.92
        assert cached_data["last_updated"] == "2026-02-10T13:00:00Z"
        assert cached_data["model_version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_subscriber_handles_incomplete_message(self):
        """Subscriber ignores messages with missing required fields."""
        # Arrange
        subscriber = CapacitySubscriber("redis://localhost:6379/0")
        subscriber.redis = AsyncMock()

        incomplete_message = {
            "type": "message",
            "data": json.dumps({
                "ticker": "AAPL",
                "score": 0.85
                # Missing confidence, timestamp, model_version
            })
        }

        # Act
        await subscriber._process_message(incomplete_message)

        # Assert
        subscriber.redis.setex.assert_not_called()  # Should not cache

    @pytest.mark.asyncio
    async def test_subscriber_handles_invalid_json(self):
        """Subscriber handles invalid JSON gracefully."""
        # Arrange
        subscriber = CapacitySubscriber("redis://localhost:6379/0")
        subscriber.redis = AsyncMock()

        invalid_message = {
            "type": "message",
            "data": "not valid json {{"
        }

        # Act (should not raise exception)
        await subscriber._process_message(invalid_message)

        # Assert
        subscriber.redis.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_subscriber_connect_and_disconnect(self):
        """Test subscriber lifecycle management."""
        # Arrange
        with patch("opa_quotes_api.services.capacity_subscriber.redis.from_url") as mock_from_url:
            mock_redis = MagicMock()
            mock_pubsub = AsyncMock()
            mock_redis.pubsub = MagicMock(return_value=mock_pubsub)
            mock_redis.close = AsyncMock()
            
            # Configure from_url to return awaitable
            async def mock_redis_factory(*args, **kwargs):
                return mock_redis
            mock_from_url.side_effect = mock_redis_factory

            subscriber = CapacitySubscriber("redis://localhost:6379/0")

            # Act: Connect
            await subscriber.connect()

            # Assert: Connected and subscribed
            mock_from_url.assert_called_once()
            mock_pubsub.subscribe.assert_called_once_with("capacity.scoring")

            # Act: Disconnect
            await subscriber.disconnect()

            # Assert: Unsubscribed and closed
            mock_pubsub.unsubscribe.assert_called_once_with("capacity.scoring")
            mock_pubsub.close.assert_called_once()
            mock_redis.close.assert_called_once()


class TestCapacityContextSchema:
    """Tests for CapacityContext Pydantic schema."""

    def test_valid_capacity_context(self):
        """Valid capacity context is parsed correctly."""
        data = {
            "score": 0.85,
            "confidence": 0.92,
            "last_updated": "2026-02-10T13:00:00Z",
            "model_version": "1.0.0"
        }

        context = CapacityContext(**data)

        assert context.score == 0.85
        assert context.confidence == 0.92
        assert context.model_version == "1.0.0"

    def test_score_validation(self):
        """Score must be between 0 and 1."""
        with pytest.raises(ValueError):
            CapacityContext(
                score=1.5,  # Invalid: > 1
                confidence=0.92,
                last_updated=datetime.now(),
                model_version="1.0.0"
            )

        with pytest.raises(ValueError):
            CapacityContext(
                score=-0.1,  # Invalid: < 0
                confidence=0.92,
                last_updated=datetime.now(),
                model_version="1.0.0"
            )

    def test_confidence_validation(self):
        """Confidence must be between 0 and 1."""
        with pytest.raises(ValueError):
            CapacityContext(
                score=0.85,
                confidence=1.2,  # Invalid: > 1
                last_updated=datetime.now(),
                model_version="1.0.0"
            )
