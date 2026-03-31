import os
from typing import Any, Dict, Literal, Mapping, Optional

from fastapi import APIRouter, Path, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.db.connection import create_db_engine
from app.db.sql.messages import (
    DELETE_MESSAGE_SQL,
    INSERT_MESSAGE_SQL,
    LIST_ALL_MESSAGES_SQL,
    LIST_MESSAGES_BY_ROOM_SQL,
    SELECT_MESSAGE_BY_ID_SQL,
    SELECT_NEXT_MESSAGE_ORDER_SQL,
    UPDATE_MESSAGE_SQL,
)
from app.db.sql.rooms import CHECK_ROOM_EXISTS_SQL


router = APIRouter(tags=["Messages"])


class MessageCreate(BaseModel):
    room_id: int = Field(ge=1)
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1)


class MessageUpdate(BaseModel):
    room_id: int = Field(ge=1)
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1)


def get_db_context() -> Dict[str, str]:
    return {
        "host": os.getenv("MYSQL_HOST", ""),
        "database": os.getenv("MYSQL_DATABASE", ""),
    }


def serialize_message(row: Mapping[str, Any]) -> Dict[str, Any]:
    message = dict(row)

    if message.get("created_at") is not None:
        message["created_at"] = message["created_at"].isoformat()

    return message


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


def room_exists(connection: Any, room_id: int) -> bool:
    row = connection.execute(
        text(CHECK_ROOM_EXISTS_SQL),
        {"room_id": room_id},
    ).first()
    return row is not None


def get_next_message_order(connection: Any, room_id: int) -> int:
    next_order = connection.execute(
        text(SELECT_NEXT_MESSAGE_ORDER_SQL),
        {"room_id": room_id},
    ).scalar()
    return int(next_order)


def fetch_message_by_id(connection: Any, message_id: int) -> Optional[Mapping[str, Any]]:
    return connection.execute(
        text(SELECT_MESSAGE_BY_ID_SQL),
        {"message_id": message_id},
    ).mappings().first()


@router.post("/messages")
def create_message(payload: MessageCreate) -> JSONResponse:
    engine: Optional[Engine] = None

    try:
        engine = create_db_engine()

        with engine.begin() as connection:
            if not room_exists(connection, payload.room_id):
                return build_error_response(
                    status.HTTP_404_NOT_FOUND,
                    f"Room {payload.room_id} not found. Create the room first.",
                )

            next_message_order = get_next_message_order(connection, payload.room_id)
            result = connection.execute(
                text(INSERT_MESSAGE_SQL),
                {
                    "room_id": payload.room_id,
                    "role": payload.role,
                    "message_order": next_message_order,
                    "content": payload.content,
                },
            )
            message_id = int(result.lastrowid)
            row = fetch_message_by_id(connection, message_id)

        response_payload = {
            "status": "ok",
            "message": "Message created successfully.",
            "data": serialize_message(row),
        }
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=jsonable_encoder(response_payload),
        )
    except IntegrityError as exc:
        root_error = str(getattr(exc, "orig", exc))

        if "Duplicate entry" in root_error:
            return build_error_response(
                status.HTTP_409_CONFLICT,
                "message_order auto assignment conflicted. Try the request again.",
            )

        return build_db_error_response(
            exc,
            "Message create failed because of a database integrity rule.",
        )
    except (ValueError, SQLAlchemyError) as exc:
        return build_db_error_response(
            exc,
            "Message create failed. Make sure the rooms/messages tables exist and the db container is running.",
        )
    finally:
        if engine is not None:
            engine.dispose()


@router.get("/messages")
def list_messages(room_id: Optional[int] = Query(default=None, ge=1)) -> JSONResponse:
    engine: Optional[Engine] = None

    try:
        engine = create_db_engine()
        query = LIST_MESSAGES_BY_ROOM_SQL if room_id is not None else LIST_ALL_MESSAGES_SQL
        params: Dict[str, Any] = {"room_id": room_id} if room_id is not None else {}

        with engine.connect() as connection:
            rows = connection.execute(text(query), params).mappings().all()

        items = [serialize_message(row) for row in rows]
        response_payload = {
            "status": "ok",
            "message": "Messages fetched successfully.",
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
            "Message list query failed. Make sure the messages table exists and the db container is running.",
        )
    finally:
        if engine is not None:
            engine.dispose()


@router.get("/messages/{message_id}")
def get_message(message_id: int = Path(ge=1)) -> JSONResponse:
    engine: Optional[Engine] = None

    try:
        engine = create_db_engine()

        with engine.connect() as connection:
            row = fetch_message_by_id(connection, message_id)

        if row is None:
            return build_error_response(status.HTTP_404_NOT_FOUND, "Message not found.")

        response_payload = {
            "status": "ok",
            "message": "Message fetched successfully.",
            "data": serialize_message(row),
        }
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(response_payload),
        )
    except (ValueError, SQLAlchemyError) as exc:
        return build_db_error_response(
            exc,
            "Message detail query failed. Make sure the messages table exists and the db container is running.",
        )
    finally:
        if engine is not None:
            engine.dispose()


@router.put("/messages/{message_id}")
def update_message(message_id: int = Path(ge=1), payload: MessageUpdate = ...) -> JSONResponse:
    engine: Optional[Engine] = None

    try:
        engine = create_db_engine()

        with engine.begin() as connection:
            existing_message = fetch_message_by_id(connection, message_id)

            if existing_message is None:
                return build_error_response(status.HTTP_404_NOT_FOUND, "Message not found.")

            if not room_exists(connection, payload.room_id):
                return build_error_response(
                    status.HTTP_404_NOT_FOUND,
                    f"Room {payload.room_id} not found. Create the room first.",
                )

            new_message_order = int(existing_message["message_order"])

            if payload.room_id != existing_message["room_id"]:
                new_message_order = get_next_message_order(connection, payload.room_id)

            result = connection.execute(
                text(UPDATE_MESSAGE_SQL),
                {
                    "room_id": payload.room_id,
                    "role": payload.role,
                    "message_order": new_message_order,
                    "content": payload.content,
                    "message_id": message_id,
                },
            )

            if result.rowcount == 0:
                return build_error_response(status.HTTP_404_NOT_FOUND, "Message not found.")

            row = fetch_message_by_id(connection, message_id)

        response_payload = {
            "status": "ok",
            "message": "Message updated successfully.",
            "data": serialize_message(row),
        }
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(response_payload),
        )
    except IntegrityError as exc:
        root_error = str(getattr(exc, "orig", exc))

        if "Duplicate entry" in root_error:
            return build_error_response(
                status.HTTP_409_CONFLICT,
                "message_order auto assignment conflicted. Try the request again.",
            )

        return build_db_error_response(
            exc,
            "Message update failed because of a database integrity rule.",
        )
    except (ValueError, SQLAlchemyError) as exc:
        return build_db_error_response(
            exc,
            "Message update failed. Make sure the rooms/messages tables exist and the db container is running.",
        )
    finally:
        if engine is not None:
            engine.dispose()


@router.delete("/messages/{message_id}")
def delete_message(message_id: int = Path(ge=1)) -> JSONResponse:
    engine: Optional[Engine] = None

    try:
        engine = create_db_engine()

        with engine.begin() as connection:
            row = fetch_message_by_id(connection, message_id)

            if row is None:
                return build_error_response(status.HTTP_404_NOT_FOUND, "Message not found.")

            connection.execute(
                text(DELETE_MESSAGE_SQL),
                {"message_id": message_id},
            )

        response_payload = {
            "status": "ok",
            "message": "Message deleted successfully.",
            "data": serialize_message(row),
        }
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(response_payload),
        )
    except (ValueError, SQLAlchemyError) as exc:
        return build_db_error_response(
            exc,
            "Message delete failed. Make sure the messages table exists and the db container is running.",
        )
    finally:
        if engine is not None:
            engine.dispose()
