"""
Redis Pub/Sub subscriber for capacity scoring integration.

Subscribes to capacity.scoring channel and caches scores in Redis
for enrichment of quote responses.
"""
import asyncio
import json

import redis.asyncio as redis

from opa_quotes_api.config import get_settings
from opa_quotes_api.logging_setup import get_logger

logger = get_logger(__name__)
settings = get_settings()


class CapacitySubscriber:
    """
    Redis Pub/Sub subscriber for capacity scoring.
    
    Subscribes to 'capacity.scoring' channel and caches received
    scores with 1-hour TTL for quote enrichment.
    """

    def __init__(self, redis_url: str | None = None):
        """
        Initialize capacity subscriber.
        
        Args:
            redis_url: Optional Redis URL (defaults to settings.redis_url)
        """
        self.redis_url = redis_url or settings.redis_url
        self.redis: redis.Redis | None = None
        self.pubsub: redis.client.PubSub | None = None
        self.channel_name = "capacity.scoring"
        self.cache_ttl = 3600  # 1 hour

    async def connect(self) -> None:
        """
        Connect to Redis and subscribe to capacity.scoring channel.
        
        Raises:
            redis.RedisError: If connection fails
        """
        try:
            self.redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe(self.channel_name)
            logger.info(f"Subscribed to Redis channel: {self.channel_name}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis Pub/Sub: {e}")
            raise

    async def listen(self) -> None:
        """
        Listen to capacity.scoring channel and cache scores.
        
        Expected message format:
        {
            "ticker": "AAPL",
            "score": 0.85,
            "confidence": 0.92,
            "timestamp": "2026-02-10T13:00:00Z",
            "model_version": "1.0.0"
        }
        
        Caches with key: capacity:score:{ticker}
        TTL: 1 hour (3600 seconds)
        """
        if not self.pubsub:
            logger.error("PubSub not initialized. Call connect() first.")
            return

        logger.info(f"Started listening on channel: {self.channel_name}")
        
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    await self._process_message(message)
        except asyncio.CancelledError:
            logger.info("Capacity subscriber task cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in capacity subscriber: {e}", exc_info=True)

    async def _process_message(self, message: dict) -> None:
        """
        Process received capacity scoring message.
        
        Args:
            message: Redis Pub/Sub message
        """
        try:
            data = json.loads(message["data"])
            
            # Validate required fields
            required_fields = ["ticker", "score", "confidence", "timestamp", "model_version"]
            if not all(field in data for field in required_fields):
                logger.warning(f"Incomplete capacity message: {data}")
                return
            
            ticker = data["ticker"]
            cache_key = f"capacity:score:{ticker}"
            
            # Prepare cache payload
            cache_payload = {
                "score": data["score"],
                "confidence": data["confidence"],
                "last_updated": data["timestamp"],
                "model_version": data["model_version"]
            }
            
            # Cache with TTL
            await self.redis.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(cache_payload)
            )
            
            logger.info(
                f"Cached capacity score for {ticker}: "
                f"score={data['score']:.2f}, "
                f"confidence={data['confidence']:.2f}"
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in capacity message: {e}")
        except Exception as e:
            logger.error(f"Error processing capacity message: {e}", exc_info=True)

    async def disconnect(self) -> None:
        """Disconnect from Redis Pub/Sub and close connections."""
        if self.pubsub:
            await self.pubsub.unsubscribe(self.channel_name)
            await self.pubsub.close()
            logger.info(f"Unsubscribed from {self.channel_name}")
        
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")
