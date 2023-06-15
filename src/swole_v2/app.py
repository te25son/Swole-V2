from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from .dependencies.settings import get_settings
from .errors.exceptions import BusinessError
from .errors.handlers import business_error_handler, http_exception_handler, request_validation_error_handler
from .routers import router as api_router
from .schemas import ErrorResponse

if TYPE_CHECKING:
    from .settings import Settings


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

        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "https://swolev2.com",
                "https://www.swolev2.com",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        app.include_router(api_router)

        return app

    def register_error_handlers(self) -> None:
        self.app.add_exception_handler(HTTPException, http_exception_handler)
        self.app.add_exception_handler(RequestValidationError, request_validation_error_handler)
        self.app.add_exception_handler(BusinessError, business_error_handler)
