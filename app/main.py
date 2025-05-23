from fastapi import FastAPI
from settings import app_config

app = FastAPI(**app_config)


@app.get("/")
def read_root():
    return {"Hello": "World"}
