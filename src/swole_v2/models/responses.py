from typing import Any

from sqlmodel import SQLModel


class Response(SQLModel):
    code: str


class ErrorResponse(Response):
    code: str = "error"
    message: str


class SuccessResponse(Response):
    code: str = "ok"
    result: list[Any] | None = None
