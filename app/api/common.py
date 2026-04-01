from typing import Any, Mapping, Optional

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.db.connection import get_db_context


def serialize_row(row: Optional[Mapping[str, Any]]) -> Optional[dict[str, Any]]:
    if row is None:
        return None

    payload = dict(row)

    for key, value in payload.items():
        if hasattr(value, "isoformat"):
            payload[key] = value.isoformat()

    return payload


def success_response(status_code: int, message: str, **payload: Any) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({"status": "ok", "message": message, **payload}),
    )


def error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({"status": "error", "message": message}),
    )


def room_not_found_response(room_id: int) -> JSONResponse:
    return error_response(
        404,
        f"Room {room_id} not found. Create the room first.",
    )


def duplicate_message_order_response() -> JSONResponse:
    return error_response(
        409,
        "message_order auto assignment conflicted. Try the request again.",
    )


def db_error_response(exc: Exception, context_message: str, status_code: int = 503) -> JSONResponse:
    db_context = get_db_context()

    if isinstance(exc, ValueError):
        payload = {
            "status": "error",
            "message": "Database settings are missing. Check your .env file and Docker Compose environment variables.",
            "host": db_context["host"],
            "database": db_context["database"],
            "error": str(exc),
        }
    else:
        payload = {
            "status": "error",
            "message": context_message,
            "host": db_context["host"],
            "database": db_context["database"],
            "error": str(getattr(exc, "orig", exc)),
        }

    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))
