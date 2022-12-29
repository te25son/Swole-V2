from typing import Any

from sqlmodel import SQLModel


class Result(SQLModel):
    success: bool
    product: list[Any] | None = None
    message: str | None = None


class Response(SQLModel):
    code: str


class ErrorResponse(Response):
    code: str = "error"
    message: str


class SuccessResponse(Response):
    code: str = "ok"
    result: Result
