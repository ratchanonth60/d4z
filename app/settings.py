from fastapi import Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware import Middleware

from app.contextmanager import lifespan
from app.core.config import settings
from app.core.dependencies import JWTBearer
from app.core.exception_handlers import (
    authentication_error_handler,
    http_exception_handler,
    internal_exception_handler,
    validation_exception_handler,
)
from app.core.exceptions import AuthenticationError

EXCLUDED_PATHS = [
    "/",  # Root path ของ app (ถ้ามี)
    "/api/v1/auth/login",  # Login endpoint
    "/api/v1/auth/refresh_token",  # Refresh token endpoint
    "/api/v1/auth/verify-email/",
    "/api/v1/auth/register",
    "/docs",
    "/openapi.json",
    "/redoc",
]

app_config = {
    "title": settings.APP_TITLE,  #
    "version": settings.APP_VERSION,  #
    "description": "API for the d4z project, structured for maintainability.",
    "lifespan": lifespan,  #
    "license_info": {
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    "exception_handlers": {
        HTTPException: http_exception_handler,  #
        RequestValidationError: validation_exception_handler,  #
        Exception: internal_exception_handler,  #
        AuthenticationError: authentication_error_handler,  #
    },
    "dependencies": [
        Depends(JWTBearer(excluded_paths=EXCLUDED_PATHS, auto_error=True))
    ],  # Uncomment และใส่ EXCLUDED_PATHS
    "middleware": [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        ),
        Middleware(GZipMiddleware, minimum_size=1000, compresslevel=5),
    ],
}
