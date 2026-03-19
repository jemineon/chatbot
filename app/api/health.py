from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.db.connection import check_db_connection


router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db")
def health_db_check() -> JSONResponse:
    db_status = check_db_connection()
    status_code = status.HTTP_200_OK if db_status["status"] == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(status_code=status_code, content=db_status)
