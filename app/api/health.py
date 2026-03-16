from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

from app.db.connection import check_db_connection


router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db")
def health_db_check() -> Dict[str, Any]:
    db_status = check_db_connection()

    if db_status["status"] != "ok":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=db_status,
        )

    return db_status
