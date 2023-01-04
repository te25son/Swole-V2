from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from .exceptions import BusinessError
from .schemas import ErrorResponse

DATABASE_ERROR = "An error occurred when performing an operation on the database with the following message. {msg}."


def http_exception_handler(request: Request, exception: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exception.status_code,
        content=ErrorResponse(message=exception.detail).dict(),
    )


def business_error_handler(request: Request, exception: BusinessError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(message=str(exception)).dict(),
    )


def request_validation_error_handler(request: Request, exception: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(message=exception.errors()[0]["msg"]).dict(),  # Only dsiplays the first error
    )


def database_operation_error_handler(request: Request, exception: SQLAlchemyError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(message=DATABASE_ERROR.format(msg=str(exception))).dict(),
    )
