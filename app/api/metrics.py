from fastapi import APIRouter, Response
from app.core.redis import cache_manager

metrics_router = APIRouter()


@metrics_router.get("/metrics")
def get_metrics():
    """
    Prometheus-compatible metrics endpoint for enterprise observability.
    Monitors high-concurrency throughput, cache hit ratios, and security enforcement events.
    """
    snapshot = cache_manager.get_metrics_snapshot()
    lines = [
        "# HELP sentinelrag_queries_total Total number of queries processed",
        "# TYPE sentinelrag_queries_total counter",
        f"sentinelrag_queries_total {snapshot.get('queries_total', 0)}",
        "",
        "# HELP sentinelrag_cache_hits_acl Total ACL cache hits",
        "# TYPE sentinelrag_cache_hits_acl counter",
        f"sentinelrag_cache_hits_acl {snapshot.get('cache_hits_acl', 0)}",
        "",
        "# HELP sentinelrag_cache_misses_acl Total ACL cache misses",
        "# TYPE sentinelrag_cache_misses_acl counter",
        f"sentinelrag_cache_misses_acl {snapshot.get('cache_misses_acl', 0)}",
        "",
        "# HELP sentinelrag_cache_hits_response Total response cache hits",
        "# TYPE sentinelrag_cache_hits_response counter",
        f"sentinelrag_cache_hits_response {snapshot.get('cache_hits_response', 0)}",
        "",
        "# HELP sentinelrag_cache_misses_response Total response cache misses",
        "# TYPE sentinelrag_cache_misses_response counter",
        f"sentinelrag_cache_misses_response {snapshot.get('cache_misses_response', 0)}",
        "",
        "# HELP sentinelrag_rate_limit_exceeded Total requests blocked by rate limiter",
        "# TYPE sentinelrag_rate_limit_exceeded counter",
        f"sentinelrag_rate_limit_exceeded {snapshot.get('rate_limit_exceeded', 0)}",
        "",
        "# HELP sentinelrag_pruned_by_acl_total Candidates pruned by answer-time ACL check",
        "# TYPE sentinelrag_pruned_by_acl_total counter",
        f"sentinelrag_pruned_by_acl_total {snapshot.get('pruned_by_acl_total', 0)}",
    ]
    return Response(content="\n".join(lines), media_type="text/plain; version=0.0.4")
