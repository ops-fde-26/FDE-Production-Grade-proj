from fastapi import FastAPI

from app import models  # noqa: F401  (registers the models on Base)
from app.config import settings
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)


@app.get("/health")
def health():
    return {
        "status": "ok",
         "app": settings.app_name,
         "debug": settings.debug
         }
