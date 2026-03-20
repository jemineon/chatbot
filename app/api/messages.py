import os
from typing import Any, Dict, Literal, Mapping, Optional

from fastapi import APIRouter, Path, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, insert, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.db.connection import create_db_engine
from app.db.schema import messages


router = APIRouter(tags=["Messages"])


class MessageCreate(BaseModel):
    room_id: int = Field(ge=1)
    role: Literal["user", "assistant", "system"]
    message_order: int = Field(ge=1)
    content: str = Field(min_length=1)


class MessageUpdate(BaseModel):
    room_id: int = Field(ge=1)
    role: Literal["user", "assistant", "system"]
    message_order: int = Field(ge=1)
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


@router.post("/messages")
def create_message(payload: MessageCreate) -> JSONResponse:
    engine: Optional[Engine] = None

    try:
        engine = create_db_engine()

        with engine.begin() as connection:
            result = connection.execute(insert(messages).values(**payload.model_dump()))
            message_id = int(result.inserted_primary_key[0])
            row = connection.execute(
                select(messages).where(messages.c.id == message_id)
            ).mappings().first()

        response_payload = {
            "status": "ok",
            "message": "Message created successfully.",
            "data": serialize_message(row),
        }
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=jsonable_encoder(response_payload),
        )
    except (ValueError, SQLAlchemyError) as exc:
        return build_db_error_response(
            exc,
            "Message create failed. Make sure the messages table exists and the db container is running.",
        )
    finally:
        if engine is not None:
            engine.dispose()


@router.get("/messages")
def list_messages(room_id: Optional[int] = Query(default=None, ge=1)) -> JSONResponse:
    engine: Optional[Engine] = None

    try:
        engine = create_db_engine()
        statement = select(messages).order_by(
            messages.c.room_id,
            messages.c.message_order,
            messages.c.id,
        )

        if room_id is not None:
            statement = statement.where(messages.c.room_id == room_id)

        with engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()

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
            row = connection.execute(
                select(messages).where(messages.c.id == message_id)
            ).mappings().first()

        if row is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"status": "error", "message": "Message not found."},
            )

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
            result = connection.execute(
                update(messages)
                .where(messages.c.id == message_id)
                .values(**payload.model_dump())
            )

            if result.rowcount == 0:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"status": "error", "message": "Message not found."},
                )

            row = connection.execute(
                select(messages).where(messages.c.id == message_id)
            ).mappings().first()

        response_payload = {
            "status": "ok",
            "message": "Message updated successfully.",
            "data": serialize_message(row),
        }
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(response_payload),
        )
    except (ValueError, SQLAlchemyError) as exc:
        return build_db_error_response(
            exc,
            "Message update failed. Make sure the messages table exists and the db container is running.",
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
            row = connection.execute(
                select(messages).where(messages.c.id == message_id)
            ).mappings().first()

            if row is None:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"status": "error", "message": "Message not found."},
                )

            connection.execute(delete(messages).where(messages.c.id == message_id))

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
