from fastapi import Request, HTTPException, Depends
from app.core.config import settings
from app.core.redis import cache_manager
from app.api.auth import get_current_identity, IdentityContext


async def rate_limiter(
    request: Request,
    identity: IdentityContext = Depends(get_current_identity),
):
    """
    High-concurrency distributed rate limiter protecting the system against overload.
    Enforces per-identity sliding window quotas across 1,000+ users.
    """
    if not settings.ENABLE_RATE_LIMITER:
        return identity

    # Give executives higher quota, interns standard quota
    limit = settings.RATE_LIMIT_PER_MINUTE
    if identity.persona == "executive":
        limit *= 2

    is_allowed, remaining, reset_seconds = cache_manager.check_rate_limit(
        identity_key=identity.user_id,
        limit=limit,
        window_seconds=60,
    )

    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {limit} requests per minute allowed.",
            headers={
                "Retry-After": str(reset_seconds),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
            },
        )

    # Attach remaining count to request state
    request.state.ratelimit_remaining = remaining
    return identity
