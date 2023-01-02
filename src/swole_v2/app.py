from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from .error_handlers import (
    business_error_handler,
    database_operation_error_handler,
    http_exception_handler,
    request_validation_error_handler,
)
from .exceptions import BusinessError
from .models import ErrorResponse
from .routers import auth, exercises, users, workouts
from .settings import Settings, get_settings


class SwoleApp:
    def __init__(self, settings: Settings = get_settings()) -> None:
        self.settings = settings
        self.app = self.create_app()
        self.register_error_handlers()

    def create_app(self) -> FastAPI:
        app = FastAPI(
            title="Swole App",
            responses={
                status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
                status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
                status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
            },
        )

        app.include_router(users.router)
        app.include_router(auth.router)
        app.include_router(workouts.router)
        app.include_router(exercises.router)

        return app

    def register_error_handlers(self) -> None:
        self.app.add_exception_handler(HTTPException, http_exception_handler)
        self.app.add_exception_handler(RequestValidationError, request_validation_error_handler)
        self.app.add_exception_handler(SQLAlchemyError, database_operation_error_handler)
        self.app.add_exception_handler(BusinessError, business_error_handler)
