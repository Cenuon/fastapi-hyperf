"""Rate Limit module — Pydantic schemas, ORM model, and CRUD."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated

from fastcrud import FastCRUD
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.db.models import SoftDeleteMixin, TimestampMixin
from app.models.base import TimestampSchema


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------


class RateLimitBase(BaseModel):
    """Base rate limit schema with common attributes."""

    path: Annotated[str, Field(examples=["/api/v1/users"])]
    limit: Annotated[int, Field(examples=[5], gt=0)]
    period: Annotated[int, Field(examples=[60], gt=0)]

    @field_validator("path")
    def validate_path_format(cls, v: str) -> str:
        """Validate path has proper API path format."""
        if not v.startswith("/"):
            raise ValueError("Path must start with a forward slash (/)")

        if not re.match(r"^\/[a-zA-Z0-9_\-\/]+$", v):
            raise ValueError("Path must be a valid API path format, e.g. /api/v1/users")

        return v


class RateLimitSchema(TimestampSchema, RateLimitBase):
    """Complete rate limit schema."""

    tier_id: int
    name: Annotated[str | None, Field(default=None, examples=["users:5:60"])]


class RateLimitSelect(BaseModel):
    """Minimal schema for selecting only required rate limit fields."""

    limit: int
    period: int


class RateLimitRead(RateLimitBase):
    """Schema for reading rate limit data."""

    id: int
    tier_id: int
    name: str
    is_deleted: bool = False


class RateLimitCreate(RateLimitBase):
    """Schema for creating a new rate limit."""

    model_config = ConfigDict(extra="forbid")
    name: Annotated[str | None, Field(default=None, examples=["api_v1_users:5:60"])]


class RateLimitCreateInternal(RateLimitCreate):
    """Internal schema for rate limit creation."""

    tier_id: int


class RateLimitUpdate(BaseModel):
    """Schema for updating rate limit information."""

    path: str | None = Field(default=None)
    limit: int | None = Field(default=None, gt=0)
    period: int | None = Field(default=None, gt=0)
    name: str | None = None

    @field_validator("path")
    def validate_path_format(cls, v: str | None) -> str | None:
        """Validate path has proper API path format."""
        if v is None:
            return None

        if not v.startswith("/"):
            raise ValueError("Path must start with a forward slash (/)")

        if not re.match(r"^\/[a-zA-Z0-9_\-\/]+$", v):
            raise ValueError("Path must be a valid API path format, e.g. /api/v1/users")

        return v


class RateLimitUpdateInternal(RateLimitUpdate):
    """Internal schema for rate limit updates."""

    updated_at: datetime


class RateLimitDelete(BaseModel):
    """Schema for deleting a rate limit."""

    pass


# ---------------------------------------------------------------------------
# ORM Model
# ---------------------------------------------------------------------------


class RateLimit(Base, TimestampMixin, SoftDeleteMixin):
    """Rate limit configuration for API endpoints."""

    __tablename__ = "rate_limits"

    id: Mapped[int] = mapped_column(
        "id",
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True,
        init=False,
    )
    tier_id: Mapped[int] = mapped_column(ForeignKey("tiers.id"), index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    path: Mapped[str] = mapped_column(String, nullable=False)
    limit: Mapped[int] = mapped_column(Integer, nullable=False)
    period: Mapped[int] = mapped_column(Integer, nullable=False)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

crud_rate_limits: FastCRUD = FastCRUD(RateLimit)
