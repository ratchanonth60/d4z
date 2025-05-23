import asyncpg
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class DBMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # ... (เหมือนเดิม) ...
        db_pool: asyncpg.Pool | None = request.app.state.get("db_pool")
        if db_pool is None:
            request.state.db_conn = None
        else:
            async with db_pool.acquire() as connection:
                request.state.db_conn = connection
                return await call_next(request)
        return await call_next(request)  # กรณี db_pool is None
