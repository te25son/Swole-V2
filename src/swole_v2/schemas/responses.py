from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Response(BaseModel):
    code: str


class ErrorResponse(Response):
    code: str = "error"
    message: str


class SuccessResponse(Response):
    code: str = "ok"
    results: list[Any] | None = Field(default=[])
