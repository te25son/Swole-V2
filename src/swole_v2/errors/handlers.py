from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ..schemas import ErrorResponse
from .exceptions import BusinessError


def http_exception_handler(_: Request, exception: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exception.status_code,
        content=ErrorResponse(message=exception.detail).dict(),
    )


def business_error_handler(_: Request, exception: BusinessError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(message=str(exception)).dict(),
    )


def request_validation_error_handler(_: Request, exception: RequestValidationError) -> JSONResponse:
    error = exception.errors()[0]
    message = f"{error['msg'].title()} ({error['loc'][1]})."
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(message=message).dict(),  # Only dsiplays the first error
    )
