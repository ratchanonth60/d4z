from contextmanager import lifespan
from core.config import settings
from fastapi import Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware import Middleware
from core.exceptions import AuthenticationError
from core.exception_handlers import (
    http_exception_handler,
    internal_exception_handler,
    validation_exception_handler,
    authentication_error_handler,
)

app_config = {
    "title": settings.APP_TITLE,
    "version": settings.APP_VERSION,
    "description": "API for the d4z project, structured for maintainability.",
    "lifespan": lifespan,  # กำหนด lifespan
    "license_info": {
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    "exception_handlers": {
        HTTPException: http_exception_handler,
        RequestValidationError: validation_exception_handler,
        Exception: internal_exception_handler,
        AuthenticationError: authentication_error_handler,
    },
    # "dependencies": [Depends(JWTBearer(excluded_paths=EXCLUDED_PATHS))],
    "middleware": [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        ),
        Middleware(GZipMiddleware, minimum_size=1000, compresslevel=5),
    ],
    # สามารถเพิ่ม configs อื่นๆ ที่มาจาก settings หรือกำหนดโดยตรง
}
