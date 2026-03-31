import os
from typing import Any, Dict, Mapping, Optional

from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import insert, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.db.connection import create_db_engine
from app.db.schema import rooms


router = APIRouter(tags=["Rooms"])


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


def get_db_context() -> Dict[str, str]:
    return {
        "host": os.getenv("MYSQL_HOST", ""),
        "database": os.getenv("MYSQL_DATABASE", ""),
    }


def serialize_room(row: Mapping[str, Any]) -> Dict[str, Any]:
    room = dict(row)

    if room.get("created_at") is not None:
        room["created_at"] = room["created_at"].isoformat()

    return room


def build_db_error_response(exc: Exception, context_message: str) -> JSONResponse:
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
        root_error = str(getattr(exc, "orig", exc))
        payload = {
            "status": "error",
            "message": context_message,
            "host": db_context["host"],
            "database": db_context["database"],
            "error": root_error,
        }

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=jsonable_encoder(payload),
    )


@router.post("/rooms")
def create_room(payload: RoomCreate) -> JSONResponse:
    engine: Optional[Engine] = None

    try:
        engine = create_db_engine()

        with engine.begin() as connection:
            result = connection.execute(insert(rooms).values(**payload.model_dump()))
            room_id = int(result.inserted_primary_key[0])
            row = connection.execute(
                select(rooms).where(rooms.c.id == room_id)
            ).mappings().first()

        response_payload = {
            "status": "ok",
            "message": "Room created successfully.",
            "data": serialize_room(row),
        }
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=jsonable_encoder(response_payload),
        )
    except (ValueError, SQLAlchemyError) as exc:
        return build_db_error_response(
            exc,
            "Room create failed. Make sure the rooms table exists and the db container is running.",
        )
    finally:
        if engine is not None:
            engine.dispose()


@router.get("/rooms")
def list_rooms() -> JSONResponse:
    engine: Optional[Engine] = None

    try:
        engine = create_db_engine()

        with engine.connect() as connection:
            rows = connection.execute(select(rooms).order_by(rooms.c.id)).mappings().all()

        items = [serialize_room(row) for row in rows]
        response_payload = {
            "status": "ok",
            "message": "Rooms fetched successfully.",
            "count": len(items),
            "items": items,
        }
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(response_payload),
        )
    except (ValueError, SQLAlchemyError) as exc:
        return build_db_error_response(
            exc,
            "Room list query failed. Make sure the rooms table exists and the db container is running.",
        )
    finally:
        if engine is not None:
            engine.dispose()
