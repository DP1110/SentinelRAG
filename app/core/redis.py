import time
import json
import logging
from typing import Optional, Tuple, Set, List, Dict, Any
from app.core.config import settings

logger = logging.getLogger("sentinelrag.redis")


class DistributedCacheManager:
    """
    Distributed Cache & State Manager backed by Redis.
    Gracefully degrades to local memory if Redis is unavailable or unconfigured.
    Guarantees consistent ACL caching, rate limiting, and response caching for 1,000+ users.
    """

    def __init__(self):
        self._redis_client = None
        self._is_redis_available = False
        self._local_acl_cache: Dict[str, Tuple[float, Set[str], bool]] = {}
        self._local_response_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self._local_rate_limit_cache: Dict[str, List[float]] = {}
        self._metrics: Dict[str, float] = {
            "queries_total": 0,
            "cache_hits_acl": 0,
            "cache_misses_acl": 0,
            "cache_hits_response": 0,
            "cache_misses_response": 0,
            "rate_limit_exceeded": 0,
            "pruned_by_acl_total": 0,
        }
        self._init_redis()

    def _init_redis(self):
        if not settings.ENABLE_REDIS:
            return
        try:
            import redis
            client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=1.0,
                socket_connect_timeout=1.0,
            )
            # Ping to verify live connection
            client.ping()
            self._redis_client = client
            self._is_redis_available = True
            logger.info("Connected to distributed Redis cluster.")
        except Exception:
            self._is_redis_available = False
            self._redis_client = None

    # --- ACL Cache ---

    def get_acl(self, doc_id: str) -> Optional[Tuple[Set[str], bool]]:
        now = time.time()
        if self._is_redis_available and self._redis_client:
            try:
                raw = self._redis_client.get(f"sentinel:acl:{doc_id}")
                if raw:
                    data = json.loads(raw)
                    self._metrics["cache_hits_acl"] += 1
                    return set(data["principals"]), data["is_active"]
                self._metrics["cache_misses_acl"] += 1
                return None
            except Exception:
                pass

        # In-memory fallback
        if doc_id in self._local_acl_cache:
            ts, principals, is_active = self._local_acl_cache[doc_id]
            if now - ts < settings.ACL_CACHE_TTL_SECONDS:
                self._metrics["cache_hits_acl"] += 1
                return principals, is_active
            else:
                del self._local_acl_cache[doc_id]

        self._metrics["cache_misses_acl"] += 1
        return None

    def set_acl(self, doc_id: str, principals: List[str], is_active: bool, ttl: int = None):
        ttl = ttl or settings.ACL_CACHE_TTL_SECONDS
        if self._is_redis_available and self._redis_client:
            try:
                payload = json.dumps({"principals": list(principals), "is_active": is_active})
                self._redis_client.setex(f"sentinel:acl:{doc_id}", ttl, payload)
                return
            except Exception:
                pass

        # In-memory fallback
        self._local_acl_cache[doc_id] = (time.time(), set(principals), is_active)

    def invalidate_acl(self, doc_id: Optional[str] = None):
        """Globally invalidates ACLs across all cluster nodes/workers."""
        if self._is_redis_available and self._redis_client:
            try:
                if doc_id:
                    self._redis_client.delete(f"sentinel:acl:{doc_id}")
                else:
                    keys = self._redis_client.keys("sentinel:acl:*")
                    if keys:
                        self._redis_client.delete(*keys)
            except Exception:
                pass

        if doc_id:
            self._local_acl_cache.pop(doc_id, None)
        else:
            self._local_acl_cache.clear()

    # --- Response Cache (Permission-Isolated) ---

    def get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        now = time.time()
        if self._is_redis_available and self._redis_client:
            try:
                raw = self._redis_client.get(cache_key)
                if raw:
                    self._metrics["cache_hits_response"] += 1
                    return json.loads(raw)
                self._metrics["cache_misses_response"] += 1
                return None
            except Exception:
                pass

        if cache_key in self._local_response_cache:
            ts, data = self._local_response_cache[cache_key]
            if now - ts < settings.RESPONSE_CACHE_TTL_SECONDS:
                self._metrics["cache_hits_response"] += 1
                return data
            else:
                del self._local_response_cache[cache_key]

        self._metrics["cache_misses_response"] += 1
        return None

    def set_cached_response(self, cache_key: str, data: Dict[str, Any], ttl: int = None):
        ttl = ttl or settings.RESPONSE_CACHE_TTL_SECONDS
        if self._is_redis_available and self._redis_client:
            try:
                self._redis_client.setex(cache_key, ttl, json.dumps(data))
                return
            except Exception:
                pass

        self._local_response_cache[cache_key] = (time.time(), data)

    def invalidate_response_cache(self):
        if self._is_redis_available and self._redis_client:
            try:
                keys = self._redis_client.keys("sentinel:resp:*")
                if keys:
                    self._redis_client.delete(*keys)
            except Exception:
                pass
        self._local_response_cache.clear()

    # --- Distributed Rate Limiting (Sliding Window) ---

    def check_rate_limit(
        self, identity_key: str, limit: int = 120, window_seconds: int = 60
    ) -> Tuple[bool, int, int]:
        """
        Sliding-window rate limiter per identity.
        Returns: (is_allowed: bool, remaining: int, reset_in_seconds: int)
        """
        now = time.time()
        key = f"sentinel:rl:{identity_key}"

        if self._is_redis_available and self._redis_client:
            try:
                pipe = self._redis_client.pipeline()
                window_start = now - window_seconds
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zadd(key, {str(now): now})
                pipe.zcard(key)
                pipe.expire(key, window_seconds)
                _, _, count, _ = pipe.execute()

                remaining = max(0, limit - count)
                is_allowed = count <= limit
                if not is_allowed:
                    self._metrics["rate_limit_exceeded"] += 1
                return is_allowed, remaining, window_seconds
            except Exception:
                pass

        # In-memory sliding window fallback
        timestamps = self._local_rate_limit_cache.get(identity_key, [])
        window_start = now - window_seconds
        valid_timestamps = [t for t in timestamps if t > window_start]
        valid_timestamps.append(now)
        self._local_rate_limit_cache[identity_key] = valid_timestamps

        count = len(valid_timestamps)
        remaining = max(0, limit - count)
        is_allowed = count <= limit
        if not is_allowed:
            self._metrics["rate_limit_exceeded"] += 1
        return is_allowed, remaining, window_seconds

    # --- Metrics ---

    def track_metric(self, name: str, value: float = 1.0):
        if name in self._metrics:
            self._metrics[name] += value

    def get_metrics_snapshot(self) -> Dict[str, Any]:
        return dict(self._metrics)


# Global singleton instance
cache_manager = DistributedCacheManager()
