import logging

from fastapi import FastAPI

from app.api.v1.routers import api_router_v1
from app.settings import app_config

log = logging.getLogger(__name__)

app = FastAPI(**app_config)

app.include_router(api_router_v1, prefix="/api")


@app.get("/")
def read_root():
    return {"Hello": "World"}
