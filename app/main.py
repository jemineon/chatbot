from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.messages import router as messages_router
from app.api.rooms import router as rooms_router


app = FastAPI(
    title="FastAPI Learning Project",
    description="A minimal FastAPI app for learning SQLAlchemy Core with MySQL in Docker Compose.",
    version="0.1.0",
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(rooms_router, prefix="/api/v1")
app.include_router(messages_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
