"""API Key module — enums, ORM models, Pydantic schemas, utilities, and CRUD."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any

from fastcrud import FastCRUD
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.models import TimestampMixin
from app.core.db.session import Base
from app.models.base import TimestampSchema


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class KeyStatus(StrEnum):
    """API key status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    REVOKED = "revoked"


class KeyPermissionResource(StrEnum):
    """API key permission resources."""

    CONVERSATIONS = "conversations"
    CREDITS = "credits"
    AI_USAGE = "ai_usage"
    USER_PROFILE = "user_profile"
    ANALYTICS = "analytics"
    ADMIN = "admin"
    BILLING = "billing"
    API_KEYS = "api_keys"
    WILDCARD = "*"


class KeyPermissionAction(StrEnum):
    """API key permission actions."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    CREATE = "create"
    UPDATE = "update"
    LIST = "list"
    ADMIN = "admin"
    WILDCARD = "*"


class KeyType(StrEnum):
    """API key type enumeration.

    Types:
        PUBLIC: Limited read-only access
        PRIVATE: Full access for user's data
        ADMIN: Administrative access
        SERVICE: Service-to-service communication
        WEBHOOK: Webhook authentication
    """

    PUBLIC = "public"
    PRIVATE = "private"
    ADMIN = "admin"
    SERVICE = "service"
    WEBHOOK = "webhook"


class HTTPMethod(StrEnum):
    """HTTP method enumeration for API key usage tracking."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


# ---------------------------------------------------------------------------
# ORM Models
# ---------------------------------------------------------------------------


class APIKey(Base, TimestampMixin):
    """API key for programmatic access."""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, init=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    key_prefix: Mapped[str] = mapped_column(String(20), index=True)
    permissions: Mapped[dict[str, Any]] = mapped_column(JSON, insert_default=dict)
    usage_limits: Mapped[dict[str, Any]] = mapped_column(JSON, insert_default=dict)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    last_used_ip: Mapped[str | None] = mapped_column(String(45), default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    key_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)

    __table_args__ = (
        Index("idx_api_keys_user_active", "user_id", "is_active"),
        Index("idx_api_keys_prefix", "key_prefix"),
        Index("idx_api_keys_expires_at", "expires_at"),
    )


class KeyUsage(Base, TimestampMixin):
    """API key usage tracking for analytics and billing."""

    __tablename__ = "key_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, init=False)
    api_key_id: Mapped[int] = mapped_column(Integer, ForeignKey("api_keys.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), index=True)
    endpoint: Mapped[str] = mapped_column(String(255), index=True)
    method: Mapped[str] = mapped_column(String(10))
    status_code: Mapped[int] = mapped_column(Integer, index=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, default=None)
    cost_microcents: Mapped[int | None] = mapped_column(BigInteger, default=None)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    ip_address: Mapped[str | None] = mapped_column(String(45), default=None)
    user_agent: Mapped[str | None] = mapped_column(Text, default=None)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    usage_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)

    __table_args__ = (
        Index("idx_key_usage_key_created", "api_key_id", "created_at"),
        Index("idx_key_usage_user_created", "user_id", "created_at"),
        Index("idx_key_usage_endpoint", "endpoint"),
        Index("idx_key_usage_status", "status_code"),
    )


class KeyPermission(Base, TimestampMixin):
    """Granular permissions for API keys."""

    __tablename__ = "key_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, init=False)
    api_key_id: Mapped[int] = mapped_column(Integer, ForeignKey("api_keys.id", ondelete="CASCADE"), index=True)
    resource: Mapped[KeyPermissionResource] = mapped_column(index=True)  # KeyPermissionResource enum values
    action: Mapped[KeyPermissionAction] = mapped_column(index=True)  # KeyPermissionAction enum values
    conditions: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    is_allowed: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        Index("idx_key_permissions_key_resource", "api_key_id", "resource", "action", unique=True),
        Index("idx_key_permissions_resource_action", "resource", "action"),
    )


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

VALID_HTTP_METHODS = {m.value for m in HTTPMethod}


class APIKeyBase(BaseModel):
    """Base schema for API key data."""

    name: Annotated[str, Field(min_length=1, max_length=100, description="Human-readable name for the API key")]
    permissions: dict[str, Any] = Field(default_factory=dict, description="Permission settings")
    usage_limits: dict[str, Any] = Field(default_factory=dict, description="Usage limits per key")
    expires_at: datetime | None = Field(default=None, description="Key expiration timestamp")
    key_metadata: dict[str, Any] | None = Field(default=None, description="Additional key metadata")


class APIKeyCreate(APIKeyBase):
    """Schema for creating a new API key."""

    pass


class APIKeyCreateInternal(APIKeyBase):
    """Internal schema for creating a new API key with additional fields."""

    user_id: int
    key_hash: str
    key_prefix: str


class APIKeyUpdate(BaseModel):
    """Schema for updating an existing API key."""

    name: Annotated[str, Field(min_length=1, max_length=100)] | None = None
    permissions: dict[str, Any] | None = None
    usage_limits: dict[str, Any] | None = None
    is_active: bool | None = None
    expires_at: datetime | None = None
    key_metadata: dict[str, Any] | None = None


class APIKeyRead(TimestampSchema, APIKeyBase):
    """Schema for reading API key data."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    key_prefix: str
    last_used_at: datetime | None
    last_used_ip: str | None
    is_active: bool


class APIKeyResponse(APIKeyRead):
    """Schema for API key creation response (includes full key)."""

    api_key: str = Field(description="Full API key - only shown once during creation")


class KeyUsageBase(BaseModel):
    """Base schema for key usage data."""

    endpoint: Annotated[str, Field(max_length=255, description="API endpoint used")]
    method: Annotated[str, Field(max_length=10, description="HTTP method")]
    status_code: Annotated[int, Field(ge=100, le=599, description="Response status code")]
    tokens_used: int | None = Field(default=None, ge=0, description="AI tokens consumed")

    cost_microcents: int | None = Field(default=None, ge=0, description="Cost in microcents")
    response_time_ms: int | None = Field(default=None, ge=0, description="Response time in milliseconds")
    ip_address: str | None = Field(default=None, max_length=45, description="Client IP address")
    user_agent: str | None = Field(default=None, description="Client user agent")
    error_message: str | None = Field(default=None, description="Error details if any")
    usage_metadata: dict[str, Any] | None = Field(default=None, description="Additional usage metadata")

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        """Validate method against HTTPMethod enum values."""
        v_upper = v.upper()
        if v_upper not in VALID_HTTP_METHODS:
            raise ValueError(f"method must be one of: {sorted(VALID_HTTP_METHODS)}")
        return v_upper


class KeyUsageCreate(KeyUsageBase):
    """Schema for creating a new key usage record."""

    api_key_id: int
    user_id: int


class KeyUsageRead(TimestampSchema, KeyUsageBase):
    """Schema for reading key usage data."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    api_key_id: int
    user_id: int


class KeyPermissionBase(BaseModel):
    """Base schema for key permission data."""

    resource: Annotated[KeyPermissionResource, Field(description="Resource type")]
    action: Annotated[KeyPermissionAction, Field(description="Action type")]
    conditions: dict[str, Any] | None = Field(default=None, description="Additional conditions")
    is_allowed: bool = Field(default=True, description="Whether permission is granted")


class KeyPermissionCreate(KeyPermissionBase):
    """Schema for creating a new key permission."""

    api_key_id: int


class KeyPermissionUpdate(BaseModel):
    """Schema for updating an existing key permission."""

    conditions: dict[str, Any] | None = None
    is_allowed: bool | None = None


class KeyPermissionRead(TimestampSchema, KeyPermissionBase):
    """Schema for reading key permission data."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    api_key_id: int


class APIKeyWithPermissions(APIKeyRead):
    """Schema for API key with its permissions."""

    permissions_list: list[KeyPermissionRead] = Field(default_factory=list, description="Detailed permissions")


class KeyUsageAnalytics(BaseModel):
    """Schema for key usage analytics."""

    api_key_id: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_tokens: int
    total_cost_microcents: int
    average_response_time_ms: float | None
    most_used_endpoints: list[dict[str, Any]]
    error_breakdown: dict[str, int]
    usage_by_day: list[dict[str, Any]]


class UserAPIKeySummary(BaseModel):
    """Schema for user API key summary."""

    user_id: int
    total_keys: int
    active_keys: int
    total_requests: int
    total_cost_microcents: int
    keys: list[APIKeyRead]


class APIKeyValidationRequest(BaseModel):
    """Schema for API key validation requests."""

    api_key: str = Field(description="API key to validate")
    resource: KeyPermissionResource = Field(description="Resource being accessed")
    action: KeyPermissionAction = Field(description="Action being performed")


class APIKeyValidationResponse(BaseModel):
    """Schema for API key validation responses."""

    is_valid: bool
    api_key_id: int | None = None
    user_id: int | None = None
    permissions: dict[str, Any] | None = None
    usage_limits: dict[str, Any] | None = None
    error_message: str | None = None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def calculate_basic_metrics(usage_records: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate basic usage metrics from usage records.

    Args:
        usage_records: List of usage record dictionaries

    Returns:
        Dictionary containing basic metrics
    """
    total_requests = len(usage_records)
    successful_requests = len([u for u in usage_records if isinstance(u, dict) and 200 <= u.get("status_code", 0) < 300])
    failed_requests = total_requests - successful_requests

    total_tokens = sum(u.get("tokens_used", 0) or 0 for u in usage_records if isinstance(u, dict))

    total_cost = sum(u.get("cost_microcents", 0) or 0 for u in usage_records if isinstance(u, dict))

    return {
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "total_tokens": total_tokens,
        "total_cost": total_cost,
    }


def calculate_response_time_metrics(usage_records: list[dict[str, Any]]) -> float | None:
    """Calculate average response time from usage records.

    Args:
        usage_records: List of usage record dictionaries

    Returns:
        Average response time in milliseconds or None if no data
    """
    response_times = []
    for u in usage_records:
        if isinstance(u, dict) and u.get("response_time_ms") is not None:
            response_times.append(u["response_time_ms"])

    return sum(response_times) / len(response_times) if response_times else None


def calculate_endpoint_usage(usage_records: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    """Calculate most used endpoints from usage records.

    Args:
        usage_records: List of usage record dictionaries
        limit: Maximum number of endpoints to return

    Returns:
        List of endpoint usage dictionaries sorted by count
    """
    endpoint_counts: dict[str, int] = {}
    for record in usage_records:
        if isinstance(record, dict):
            endpoint = record.get("endpoint", "")
            endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1

    return [
        {"endpoint": endpoint, "count": count}
        for endpoint, count in sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    ]


def calculate_error_breakdown(usage_records: list[dict[str, Any]]) -> dict[str, int]:
    """Calculate error status code breakdown from usage records.

    Args:
        usage_records: List of usage record dictionaries

    Returns:
        Dictionary mapping status codes to counts
    """
    error_counts: dict[str, int] = {}
    for record in usage_records:
        if isinstance(record, dict) and record.get("status_code", 0) >= 400:
            status = record.get("status_code", 0)
            error_counts[str(status)] = error_counts.get(str(status), 0) + 1

    return error_counts


def calculate_daily_usage(usage_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Calculate daily usage breakdown from usage records.

    Args:
        usage_records: List of usage record dictionaries

    Returns:
        List of daily usage dictionaries sorted by date
    """
    daily_usage: dict[str, dict[str, Any]] = {}

    for record in usage_records:
        if not isinstance(record, dict) or not record.get("created_at"):
            continue

        created_at = record["created_at"]
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue

        day_key = created_at.strftime("%Y-%m-%d")
        if day_key not in daily_usage:
            daily_usage[day_key] = {
                "date": day_key,
                "requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "tokens": 0,
                "cost_microcents": 0,
            }

        daily_usage[day_key]["requests"] += 1
        if 200 <= record.get("status_code", 0) < 300:
            daily_usage[day_key]["successful_requests"] += 1
        else:
            daily_usage[day_key]["failed_requests"] += 1
        daily_usage[day_key]["tokens"] += record.get("tokens_used", 0) or 0
        daily_usage[day_key]["cost_microcents"] += record.get("cost_microcents", 0) or 0

    return sorted(daily_usage.values(), key=lambda x: x["date"])


def parse_usage_records(result: Any) -> list[dict[str, Any]]:
    """Parse usage records from database result.

    Args:
        result: Database query result

    Returns:
        List of usage record dictionaries
    """
    usage_records: list[dict[str, Any]] = []
    if isinstance(result, dict) and result.get("data"):
        data = result["data"]
        if isinstance(data, list):
            usage_records = data

    return usage_records


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

crud_api_keys: FastCRUD = FastCRUD(APIKey)
crud_key_usage: FastCRUD = FastCRUD(KeyUsage)
crud_key_permissions: FastCRUD = FastCRUD(KeyPermission)
