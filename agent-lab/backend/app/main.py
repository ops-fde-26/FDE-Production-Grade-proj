from fastapi import FastAPI

from app import models  # noqa: F401  (registers the models on Base)
from app.config import settings
from app.database import Base, engine
from app.routers import chat, conversations

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)
app.include_router(conversations.router)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
         "app": settings.app_name,
         "debug": settings.debug
         }
