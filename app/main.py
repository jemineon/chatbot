from fastapi import FastAPI

from app.api.health import router as health_router


app = FastAPI(
    title="FastAPI Learning Project",
    description="A minimal FastAPI skeleton for study.",
    version="0.1.0",
)

app.include_router(health_router, prefix="/api/v1")
