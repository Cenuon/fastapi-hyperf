"""Tier API endpoints."""

from typing import Any

from fastapi import HTTPException
from fastcrud import compute_offset

from app.core.auth.http_exceptions import NotFoundException
from app.core.dependencies import AsyncSessionDep
from app.models.base import PaginatedData
from app.models.tier import TierRead, crud_tiers
from app.services.tier import TierServiceDep
from app.utils.exceptions import TierNotFoundError
from app.utils.error_handler import handle_exception
from app.utils.response import create_unified_router, unified_paginated_response

router = create_unified_router(tags=["Tiers"])


@router.get("/", response_model=PaginatedData[TierRead], summary="List tiers")
async def get_tiers(
    db: AsyncSessionDep,
    tier_service: TierServiceDep,
    page: int = 1,
    items_per_page: int = 10,
) -> dict:
    """Paginated list of tiers."""
    try:
        tiers_data = await tier_service.get_all(
            db=db,
            skip=compute_offset(page, items_per_page),
            limit=items_per_page,
        )
        return unified_paginated_response(crud_data=tiers_data, page=page, items_per_page=items_per_page)
    except Exception as e:
        http_exception = handle_exception(e)
        if http_exception:
            raise http_exception
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/{name}", response_model=TierRead, summary="Get a tier by name")
async def get_tier_by_name(
    name: str,
    db: AsyncSessionDep,
    tier_service: TierServiceDep,
) -> dict[str, Any]:
    """Get a tier by name."""
    try:
        return await tier_service.get_by_name(name, db)
    except TierNotFoundError:
        raise NotFoundException("Tier not found")
    except Exception as e:
        http_exception = handle_exception(e)
        if http_exception:
            raise http_exception
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
