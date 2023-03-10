from typing import Any

from pydantic import BaseModel


class Response(BaseModel):
    code: str


class ErrorResponse(Response):
    code: str = "error"
    message: str


class SuccessResponse(Response):
    code: str = "ok"
    results: list[Any] | None = None
