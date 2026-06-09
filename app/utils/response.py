"""Unified API response utilities.

Provides a custom APIRoute that wraps all successful responses into
``{code, message, data}`` envelope and helper functions for creating
unified routers and paginated responses.
"""

import json
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute


class UnifiedResponseRoute(APIRoute):
    """Custom route class that wraps all JSON responses into the unified envelope.

    Non-JSON responses (``RedirectResponse``, ``StreamingResponse``) are
    passed through unchanged.  Responses that already contain the envelope
    keys are also left untouched (idempotency guard).
    """

    def get_route_handler(self) -> Any:
        original_route_handler = super().get_route_handler()

        async def unified_handler(request: Request) -> Response:
            response = await original_route_handler(request)

            # Passthrough non-JSON responses (RedirectResponse, etc.)
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                return response

            return self._wrap_response(response)

        return unified_handler

    @staticmethod
    def _wrap_response(response: Response) -> JSONResponse:
        """Wrap a JSON response body into the ``{code, message, data}`` envelope."""
        status_code = response.status_code

        # 204 No Content -> 200 with null data
        if status_code == 204:
            wrapped = JSONResponse(
                status_code=200,
                content={"code": 200, "message": "success", "data": None},
            )
            _copy_headers(response, wrapped)
            return wrapped

        # Decode the original body
        body = response.body
        if isinstance(body, bytes):
            body = body.decode("utf-8")

        try:
            original_data = json.loads(body)
        except (json.JSONDecodeError, TypeError):
            # Unable to parse – return as-is
            return response  # type: ignore[return-value]

        # Idempotency: skip if already wrapped
        if (
            isinstance(original_data, dict)
            and "code" in original_data
            and "message" in original_data
            and "data" in original_data
            and len(original_data) == 3
        ):
            return response  # type: ignore[return-value]

        wrapped = JSONResponse(
            status_code=status_code,
            content={
                "code": status_code,
                "message": "success",
                "data": original_data,
            },
        )
        _copy_headers(response, wrapped)
        return wrapped


def _copy_headers(source: Response, target: Response) -> None:
    """Copy relevant headers (especially set-cookie) from *source* to *target*."""
    for key, value in source.headers.items():
        if key.lower() not in ("content-type", "content-length"):
            target.headers[key] = value


def create_unified_router(**kwargs: Any) -> APIRouter:
    """Create an ``APIRouter`` that uses ``UnifiedResponseRoute`` for all routes."""
    return APIRouter(route_class=UnifiedResponseRoute, **kwargs)


def unified_paginated_response(
    crud_data: dict[str, Any],
    page: int,
    items_per_page: int,
    multi_response_key: str = "data",
) -> dict[str, Any]:
    """Transform fastcrud paginated data into the standard ``data`` payload.

    Maps fastcrud fields to the unified schema:
    - ``data``     -> ``items``
    - ``total_count`` -> ``total``
    - ``items_per_page`` -> ``size``
    """
    items = crud_data.get(multi_response_key, [])
    total_count = crud_data.get("total_count", 0)
    return {
        "items": items,
        "total": total_count,
        "page": page,
        "size": items_per_page,
        "has_more": (page * items_per_page) < total_count,
    }
