import os
from typing import Any, Dict, Mapping, Optional

from fastapi import APIRouter, Path, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.db.connection import create_db_engine
from app.db.sql.rooms import (
    CHECK_ROOM_HAS_MESSAGES_SQL,
    DELETE_ROOM_SQL,
    INSERT_ROOM_SQL,
    LIST_ROOMS_SQL,
    SELECT_ROOM_BY_ID_SQL,
)


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


def build_error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({"status": "error", "message": message}),
    )


def fetch_room_by_id(connection: Any, room_id: int) -> Optional[Mapping[str, Any]]:
    return connection.execute(
        text(SELECT_ROOM_BY_ID_SQL),
        {"room_id": room_id},
    ).mappings().first()


@router.post("/rooms")
def create_room(payload: RoomCreate) -> JSONResponse:
    engine: Optional[Engine] = None

    try:
        engine = create_db_engine()

        with engine.begin() as connection:
            result = connection.execute(
                text(INSERT_ROOM_SQL),
                {"name": payload.name},
            )
            room_id = int(result.lastrowid)
            row = fetch_room_by_id(connection, room_id)

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
            rows = connection.execute(text(LIST_ROOMS_SQL)).mappings().all()

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


@router.get("/rooms/{room_id}")
def get_room(room_id: int = Path(ge=1)) -> JSONResponse:
    engine: Optional[Engine] = None

    try:
        engine = create_db_engine()

        with engine.connect() as connection:
            row = fetch_room_by_id(connection, room_id)

        if row is None:
            return build_error_response(status.HTTP_404_NOT_FOUND, "Room not found.")

        response_payload = {
            "status": "ok",
            "message": "Room fetched successfully.",
            "data": serialize_room(row),
        }
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(response_payload),
        )
    except (ValueError, SQLAlchemyError) as exc:
        return build_db_error_response(
            exc,
            "Room detail query failed. Make sure the rooms table exists and the db container is running.",
        )
    finally:
        if engine is not None:
            engine.dispose()


@router.delete("/rooms/{room_id}")
def delete_room(room_id: int = Path(ge=1)) -> JSONResponse:
    engine: Optional[Engine] = None

    try:
        engine = create_db_engine()

        with engine.begin() as connection:
            room_row = fetch_room_by_id(connection, room_id)

            if room_row is None:
                return build_error_response(status.HTTP_404_NOT_FOUND, "Room not found.")

            message_row = connection.execute(
                text(CHECK_ROOM_HAS_MESSAGES_SQL),
                {"room_id": room_id},
            ).first()

            if message_row is not None:
                return build_error_response(
                    status.HTTP_409_CONFLICT,
                    "Room cannot be deleted because messages still exist in it. Delete the messages first.",
                )

            connection.execute(
                text(DELETE_ROOM_SQL),
                {"room_id": room_id},
            )

        response_payload = {
            "status": "ok",
            "message": "Room deleted successfully.",
            "data": serialize_room(room_row),
        }
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(response_payload),
        )
    except (ValueError, SQLAlchemyError) as exc:
        return build_db_error_response(
            exc,
            "Room delete failed. Make sure the rooms table exists and the db container is running.",
        )
    finally:
        if engine is not None:
            engine.dispose()
