from fastapi import APIRouter

from app.api.v1.endpoints import auth, users

api_router_v1 = APIRouter(prefix="/v1")
api_router_v1.include_router(users.router, prefix="/users", tags=["Users"])
api_router_v1.include_router(auth.router, prefix="/auth", tags=["Auth"])
