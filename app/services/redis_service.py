from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json
import structlog
from aioredis import Redis

from app.core.config import settings
from app.models import Bin, WebSocketMessage

logger = structlog.get_logger(__name__)


class RedisService:
    """Redis caching service for MQTT messages and frequently accessed data."""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.default_ttl = settings.redis_cache_ttl

    async def cache_bin_status(self, bin_id: str, bin_data: Dict[str, Any]):
        """Cache bin status data with TTL."""
        key = f"bin:status:{bin_id}"
        try:
            await self.redis.setex(
                key, self.default_ttl, json.dumps(bin_data, default=str)
            )
            logger.info(f"Cached status for bin {bin_id}")
        except Exception as e:
            logger.error(f"Failed to cache bin status {bin_id}: {e}")

    async def get_cached_bin_status(self, bin_id: str) -> Optional[Dict[str, Any]]:
        """Get cached bin status."""
        key = f"bin:status:{bin_id}"
        try:
            cached_data = await self.redis.get(key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get cached status for bin {bin_id}: {e}")
            return None

    async def cache_mqtt_message(self, topic: str, message: Dict[str, Any]):
        """Cache MQTT message for real-time updates."""
        key = f"mqtt:message:{topic}"
        try:
            await self.redis.setex(
                key,
                300,  # 5 minutes TTL for MQTT messages
                json.dumps(message, default=str),
            )
        except Exception as e:
            logger.error(f"Failed to cache MQTT message {topic}: {e}")

    async def get_recent_mqtt_messages(self, bin_id: str, limit: int = 10):
        """Get recent MQTT messages for a specific bin."""
        key_pattern = f"mqtt:message:waste_bins/{bin_id}/*"
        try:
            keys = await self.redis.keys(key_pattern)
            if not keys:
                return []

            messages = []
            for key in keys[:limit]:
                message = await self.redis.get(key)
                if message:
                    messages.append(json.loads(message))

            return messages
        except Exception as e:
            logger.error(f"Failed to get recent MQTT messages for {bin_id}: {e}")
            return []

    async def cache_analytics_data(self, data_type: str, data: Dict[str, Any]):
        """Cache analytics data for dashboard."""
        key = f"analytics:{data_type}"
        try:
            await self.redis.setex(
                key,
                1800,  # 30 minutes TTL for analytics
                json.dumps(data, default=str),
            )
        except Exception as e:
            logger.error(f"Failed to cache analytics {data_type}: {e}")

    async def get_cached_analytics(self, data_type: str) -> Optional[Dict[str, Any]]:
        """Get cached analytics data."""
        key = f"analytics:{data_type}"
        try:
            cached_data = await self.redis.get(key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get cached analytics {data_type}: {e}")
            return None

    async def cache_detection_results(self, bin_id: str, results: Dict[str, Any]):
        """Cache YOLO detection results."""
        key = f"detection:{bin_id}"
        try:
            await self.redis.setex(
                key,
                900,  # 15 minutes TTL for detections
                json.dumps(results, default=str),
            )
        except Exception as e:
            logger.error(f"Failed to cache detection results for {bin_id}: {e}")

    async def get_cached_detection(self, bin_id: str) -> Optional[Dict[str, Any]]:
        """Get cached detection results."""
        key = f"detection:{bin_id}"
        try:
            cached_data = await self.redis.get(key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get cached detection for {bin_id}: {e}")
            return None

    async def increment_rate_limit(self, key: str, window: int = 60) -> int:
        """Rate limiting using Redis."""
        try:
            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, window)
            return current
        except Exception as e:
            logger.error(f"Rate limit error for key {key}: {e}")
            return 0

    async def clear_bin_cache(self, bin_id: str):
        """Clear all cached data for a specific bin."""
        patterns = [
            f"bin:status:{bin_id}",
            f"detection:{bin_id}",
            f"mqtt:message:waste_bins/{bin_id}/*",
        ]

        try:
            for pattern in patterns:
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
            logger.info(f"Cleared cache for bin {bin_id}")
        except Exception as e:
            logger.error(f"Failed to clear cache for bin {bin_id}: {e}")

    async def get_all_critical_bins(self) -> List[str]:
        """Get all bin IDs with critical fill levels (>80%)."""
        try:
            keys = await self.redis.keys("bin:status:*")
            critical_bins = []

            for key in keys:
                cached_data = await self.redis.get(key)
                if cached_data:
                    bin_data = json.loads(cached_data)
                    if bin_data.get("fill_level", 0) > 80:
                        bin_id = key.split(":")[-1]
                        critical_bins.append(bin_id)

            return critical_bins
        except Exception as e:
            logger.error(f"Failed to get critical bins: {e}")
            return []

    async def set_websocket_connection(self, connection_id: str, user_id: str):
        """Track active WebSocket connections."""
        key = f"ws:connection:{connection_id}"
        try:
            await self.redis.setex(key, 3600, user_id)  # 1 hour TTL
        except Exception as e:
            logger.error(f"Failed to track WebSocket connection {connection_id}: {e}")

    async def remove_websocket_connection(self, connection_id: str):
        """Remove WebSocket connection tracking."""
        key = f"ws:connection:{connection_id}"
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Failed to remove WebSocket connection {connection_id}: {e}")
