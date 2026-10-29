import hashlib
from typing import List, Optional, Dict, Any
from app.core.redis import cache_manager
from app.core.config import settings


def compute_principals_hash(principals: List[str]) -> str:
    """
    Computes a deterministic hash of the user's active principal set.
    Ensures mathematical isolation between distinct permission boundaries.
    """
    canonical_str = ",".join(sorted(list(set(principals))))
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()[:16]


def compute_query_hash(query: str) -> str:
    """Computes a normalized hash of the user question."""
    normalized = " ".join(query.strip().lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def get_cached_rag_response(principals: List[str], query: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves cached response scoped to the requester's exact principal set.
    Prevents cache cross-contamination (PRD S9).
    """
    if not settings.ENABLE_RESPONSE_CACHE:
        return None

    p_hash = compute_principals_hash(principals)
    q_hash = compute_query_hash(query)
    cache_key = f"sentinel:resp:{p_hash}:{q_hash}"
    return cache_manager.get_cached_response(cache_key)


def set_cached_rag_response(
    principals: List[str], query: str, response_data: Dict[str, Any], ttl: Optional[int] = None
):
    """
    Caches RAG response under a key scoped strictly to the caller's principal set.
    """
    if not settings.ENABLE_RESPONSE_CACHE:
        return

    p_hash = compute_principals_hash(principals)
    q_hash = compute_query_hash(query)
    cache_key = f"sentinel:resp:{p_hash}:{q_hash}"
    cache_manager.set_cached_response(cache_key, response_data, ttl)
