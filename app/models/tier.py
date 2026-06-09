"""Tier module — Pydantic schemas, ORM model, and CRUD."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Annotated

from fastcrud import FastCRUD
from pydantic import BaseModel, Field
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.models import SoftDeleteMixin, TimestampMixin
from app.core.db.session import Base
from app.models.base import TimestampSchema

if TYPE_CHECKING:
    from app.models.user import User


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------


class TierBase(BaseModel):
    """Base tier schema with common attributes."""

    name: Annotated[
        str,
        Field(
            description="Name of the tier",
            examples=["free", "basic", "pro", "enterprise"],
            min_length=1,
            max_length=50,
        ),
    ]


class TierSchema(TimestampSchema, TierBase):
    """Complete tier schema with timestamps."""

    pass


class TierSelect(BaseModel):
    """Minimal schema for selecting only required tier fields."""

    id: int
    name: str


class TierRead(TierBase):
    """Schema for reading tier data."""

    id: int
    created_at: datetime
    description: str | None = None
    is_deleted: bool = False


class TierCreate(TierBase):
    """Schema for creating a new tier."""

    description: Annotated[
        str | None,
        Field(
            description="Description of the tier",
            max_length=500,
            default=None,
        ),
    ]


class TierCreateInternal(TierCreate):
    """Internal schema for tier creation."""

    pass


class TierUpdate(BaseModel):
    """Schema for updating tier information."""

    name: Annotated[
        str | None,
        Field(
            description="Name of the tier",
            min_length=1,
            max_length=50,
            default=None,
        ),
    ]
    description: Annotated[
        str | None,
        Field(
            description="Description of the tier",
            max_length=500,
            default=None,
        ),
    ]


class TierUpdateInternal(TierUpdate):
    """Internal schema for tier updates."""

    updated_at: datetime


class TierDelete(BaseModel):
    """Schema for deleting a tier."""

    pass


# ---------------------------------------------------------------------------
# ORM Model
# ---------------------------------------------------------------------------


class Tier(Base, TimestampMixin, SoftDeleteMixin):
    """Tier model — bare model for user categorization. No business logic, no pricing."""

    __tablename__ = "tiers"

    id: Mapped[int] = mapped_column(
        "id",
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True,
        init=False,
    )
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, default=None)

    users: Mapped[list["User"]] = relationship("User", back_populates="tier", lazy="selectin", default_factory=list, init=False)

    def __repr__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

crud_tiers: FastCRUD = FastCRUD(Tier)
