from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import (
    HTTPException as StarletteHTTPException,
)  # สำคัญ: ใช้ตัวนี้สำหรับ HTTPException ทั่วไป

from .exceptions import (
    AuthenticationError,
    AuthorizationError,
)  # Import custom exceptions ของเรา


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handler for Starlette's HTTPException.
    FastAPI's default behavior for HTTPException is usually sufficient,
    but this allows for custom logging or response structure if needed.
    """
    # print(f"Starlette HTTPException handled: {exc.detail}") # ตัวอย่างการ log
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),  # ถ้ามี headers ใน exception ก็ส่งไปด้วย
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler for FastAPI's RequestValidationError (Pydantic validation errors).
    This reformats the error messages for a more user-friendly output.
    """
    errors = []
    for error in exc.errors():
        field = (
            " -> ".join(str(loc) for loc in error["loc"]) if error["loc"] else "general"
        )
        errors.append({"field": field, "message": error["msg"], "type": error["type"]})
    # print(f"Request Validation Error: {errors}") # ตัวอย่างการ log
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation Error", "errors": errors},
    )


async def internal_exception_handler(request: Request, exc: Exception):
    """
    Handler for generic Python Exceptions (catch-all for unexpected errors).
    Important: Log the actual exception for debugging, but return a generic error to the client.
    """
    # ควร log exception `exc` อย่างละเอียดที่นี่สำหรับทีมพัฒนา
    # เช่น: import logging; logging.error("Unhandled exception:", exc_info=exc)
    print(f"Unhandled internal exception: {exc}")  # ตัวอย่างการ log แบบง่าย
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."},
    )


async def authentication_error_handler(request: Request, exc: AuthenticationError):
    """
    Handler for our custom AuthenticationError.
    """
    # print(f"Authentication Error: {exc.detail}") # ตัวอย่างการ log
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.detail},
        headers={"WWW-Authenticate": "Bearer"},  # Optional: ถ้าใช้ Bearer token
    )


async def authorization_error_handler(request: Request, exc: AuthorizationError):
    """
    Handler for our custom AuthorizationError.
    """
    # print(f"Authorization Error: {exc.detail}") # ตัวอย่างการ log
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exc.detail},
    )
