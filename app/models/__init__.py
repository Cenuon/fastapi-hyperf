"""Register all models with Base.metadata."""
from app.models.user import User  # noqa: F401
from app.models.tier import Tier  # noqa: F401
from app.models.api_key import APIKey, KeyPermission, KeyUsage  # noqa: F401
from app.models.rate_limit import RateLimit  # noqa: F401
