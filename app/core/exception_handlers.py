import logging

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.base_response import (  # สำคัญ: ใช้ตัวนี้สำหรับ HTTPException ทั่วไป
    ErrorDetail,
    ErrorResponse,
)

from .exceptions import (  # Import custom exceptions ของเรา
    AuthenticationError,
    AuthorizationError,
)

log = logging.getLogger(__name__)  # สำหรับ log


async def http_exception_handler(
    _: Request, exc: HTTPException
):  # ใช้ HTTPException ของ FastAPI ได้
    """
    Handler for FastAPI's HTTPException.
    Returns response in standard ErrorResponse format.
    """
    log.error(f"HTTPException: {exc.detail}")  # Log error message
    error_resp = ErrorResponse(
        code=exc.status_code,
        message=exc.detail,
        errors=[ErrorDetail(message=exc.detail)],  # หรือจะใส่ detail ใน errors list ก็ได้
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=error_resp.model_dump(exclude_none=True),  # Pydantic V2+
        headers=exc.headers,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler for FastAPI's RequestValidationError (Pydantic validation errors).
    This reformats the error messages into our standard ErrorResponse.
    """
    error_details = []
    for error in exc.errors():
        field = (
            " -> ".join(str(loc) for loc in error["loc"]) if error["loc"] else "general"
        )
        error_details.append(
            ErrorDetail(field=field, message=error["msg"], type=error["type"])
        )

    error_resp = ErrorResponse(message="Validation Error", errors=error_details)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=error_resp.model_dump(exclude_none=True),  # Pydantic V2+
    )


async def internal_exception_handler(request: Request, exc: Exception):
    """
    Handler for generic Python Exceptions (catch-all for unexpected errors).
    Important: Log the actual exception for debugging, but return a generic error to the client.
    """
    # import traceback
    # traceback.print_exc() # สำหรับดู stack trace ตอน debug
    log.error(f"Unhandled internal exception: {exc}")  # Log error message
    error_resp = ErrorResponse(
        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="An unexpected internal server error occurred.",
        # errors=[ErrorDetail(message=str(exc))] # Optional: ถ้าต้องการส่งรายละเอียด error (ระวัง sensitive info)
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=error_resp.model_dump(exclude_none=True),  # Pydantic V2+
    )


async def authentication_error_handler(request: Request, exc: AuthenticationError):  #
    """
    Handler for our custom AuthenticationError.
    """
    error_resp = ErrorResponse(
        code=status.HTTP_401_UNAUTHORIZED,  # ใช้ 401 แทน 403
        message=exc.detail,
        errors=[ErrorDetail(message=exc.detail)],
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=error_resp.model_dump(exclude_none=True),  # Pydantic V2+
        headers={"WWW-Authenticate": "Bearer"},
    )


async def authorization_error_handler(request: Request, exc: AuthorizationError):  #
    """
    Handler for our custom AuthorizationError.
    """
    error_resp = ErrorResponse(
        code=status.HTTP_403_FORBIDDEN,  # ใช้ 403 แทน 401
        message=exc.detail,
        errors=[ErrorDetail(message=exc.detail)],
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=error_resp.model_dump(exclude_none=True),  # Pydantic V2+
    )
