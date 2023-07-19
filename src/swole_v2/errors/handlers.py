from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import status
from fastapi.responses import JSONResponse

from ..schemas import ErrorResponse

if TYPE_CHECKING:
    from fastapi import HTTPException, Request
    from fastapi.exceptions import RequestValidationError

    from .exceptions import BusinessError


def http_exception_handler(_: Request, exception: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exception.status_code,
        content=ErrorResponse(message=exception.detail).model_dump(),
    )


def business_error_handler(_: Request, exception: BusinessError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(message=str(exception)).model_dump(),
    )


def request_validation_error_handler(_: Request, exception: RequestValidationError) -> JSONResponse:
    error = exception.errors()[0]
    message = f"{error['msg'].title()}. Hint: {error['loc']}.".replace("'", "").replace(",", " >")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(message=message).model_dump(),  # Only dsiplays the first error
    )
