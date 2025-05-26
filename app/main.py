import logging
import sys  # For stdout

from fastapi import FastAPI

from app.api.v1.routers import api_router_v1
from app.settings import app_config

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,  # Adjust level as needed (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Output to console, suitable for Docker
        # You can add FileHandler here if you want to log to files
        # logging.FileHandler("app.log"),
    ],
)
app = FastAPI(**app_config)

app.include_router(api_router_v1, prefix="/api")


@app.get("/")
def read_root():
    return {"Hello": "World"}
