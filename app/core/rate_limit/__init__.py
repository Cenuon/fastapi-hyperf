"""Rate limiter infrastructure.

This module contains the rate limiting infrastructure components, including middleware
and backend implementations.
"""

import importlib.util

from app.core.rate_limit.base import RateLimiterBackend
from app.core.rate_limit.exceptions import RateLimiterBackendException, RateLimitException
from .initialize import close_rate_limiter, initialize_rate_limiter
from app.middleware.rate_limit import RateLimiterMiddleware, _check_rate_limit, check_rate_limit
from app.core.rate_limit.provider import get_count, increment_and_check, rate_limiter_provider, reset
from app.core.rate_limit.utils import sanitize_path

MEMCACHED_INSTALLED = importlib.util.find_spec("aiomcache") is not None
REDIS_INSTALLED = importlib.util.find_spec("redis") is not None

__all__ = [
    "RateLimiterMiddleware",
    "check_rate_limit",
    "_check_rate_limit",
    "RateLimitException",
    "RateLimiterBackendException",
    "rate_limiter_provider",
    "increment_and_check",
    "get_count",
    "reset",
    "initialize_rate_limiter",
    "close_rate_limiter",
    "sanitize_path",
    "RateLimiterBackend",
    "MEMCACHED_INSTALLED",
    "REDIS_INSTALLED",
]
