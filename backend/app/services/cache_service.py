"""Redis cache service for search results"""
import logging
import hashlib
import json
from typing import Optional, Dict, Any
from uuid import UUID
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Service for managing Redis cache operations"""

    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.ttl = settings.CACHE_TTL_SECONDS

    def connect(self):
        """Initialize Redis client with connection pooling"""
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                max_connections=50
            )
            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def _generate_cache_key(self, tenant_id: UUID, query: str, page: int, size: int) -> str:
        """Generate cache key for search query"""
        # Normalize query (lowercase, strip whitespace)
        normalized_query = query.lower().strip()

        # Create hash of query parameters
        key_parts = f"{tenant_id}:{normalized_query}:{page}:{size}"
        query_hash = hashlib.md5(key_parts.encode()).hexdigest()

        return f"search:{tenant_id}:{query_hash}"

    def get_search_result(
        self,
        tenant_id: UUID,
        query: str,
        page: int,
        size: int
    ) -> Optional[Dict[str, Any]]:
        """Get cached search results"""
        if not self.client:
            return None

        cache_key = self._generate_cache_key(tenant_id, query, page, size)

        try:
            cached_data = self.client.get(cache_key)
            if cached_data:
                logger.info(f"Cache HIT for key: {cache_key}")
                return json.loads(cached_data)
            else:
                logger.info(f"Cache MISS for key: {cache_key}")
                return None
        except Exception as e:
            logger.error(f"Failed to get from cache: {e}")
            return None

    def set_search_result(
        self,
        tenant_id: UUID,
        query: str,
        page: int,
        size: int,
        result: Dict[str, Any]
    ) -> bool:
        """Cache search results with TTL"""
        if not self.client:
            return False

        cache_key = self._generate_cache_key(tenant_id, query, page, size)

        try:
            serialized = json.dumps(result)
            self.client.setex(cache_key, self.ttl, serialized)
            logger.info(f"Cached results for key: {cache_key} (TTL: {self.ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
            return False

    def invalidate_tenant_cache(self, tenant_id: UUID) -> bool:
        """Invalidate all cache entries for a tenant"""
        if not self.client:
            return False

        try:
            # Pattern to match all search queries for this tenant
            pattern = f"search:{tenant_id}:*"

            # Scan for matching keys
            keys = []
            cursor = 0
            while True:
                cursor, partial_keys = self.client.scan(cursor, match=pattern, count=100)
                keys.extend(partial_keys)
                if cursor == 0:
                    break

            if keys:
                self.client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries for tenant {tenant_id}")

            return True
        except Exception as e:
            logger.error(f"Failed to invalidate cache for tenant {tenant_id}: {e}")
            return False

    def invalidate_document_cache(self, tenant_id: UUID, document_id: UUID) -> bool:
        """Invalidate cache when a document is updated or deleted"""
        # For simplicity, invalidate all tenant cache
        # In production, could be more selective based on document content
        return self.invalidate_tenant_cache(tenant_id)

    def health_check(self) -> str:
        """Check Redis health"""
        try:
            if self.client:
                self.client.ping()
                return "up"
            return "down"
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return "down"

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.client:
            return {}

        try:
            info = self.client.info('stats')
            return {
                "total_commands": info.get('total_commands_processed', 0),
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                )
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}

    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)

    def close(self):
        """Close Redis connection"""
        if self.client:
            self.client.close()
            logger.info("Redis client closed")


# Singleton instance
cache_service = CacheService()
