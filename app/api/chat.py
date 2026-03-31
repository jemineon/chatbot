from typing import Literal, Optional

from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.api.messages import (
    build_db_error_response,
    build_error_response,
    fetch_message_by_id,
    get_next_message_order,
    room_exists,
    serialize_message,
)
from app.db.connection import create_db_engine
from app.db.sql.messages import INSERT_MESSAGE_SQL


router = APIRouter(tags=["Chat"])


class ChatRequest(BaseModel):
    room_id: int = Field(ge=1)
    content: str = Field(min_length=1)
    assistant_mode: Literal["echo"] = "echo"


def build_assistant_reply(user_content: str, assistant_mode: str) -> str:
    if assistant_mode == "echo":
        return f"Echo: {user_content}"

    return "Assistant mode is not supported."


@router.post("/chat")
def chat(payload: ChatRequest) -> JSONResponse:
    engine: Optional[Engine] = None

    try:
        engine = create_db_engine()

        with engine.begin() as connection:
            if not room_exists(connection, payload.room_id):
                return build_error_response(
                    status.HTTP_404_NOT_FOUND,
                    f"Room {payload.room_id} not found. Create the room first.",
                )

            user_message_order = get_next_message_order(connection, payload.room_id)
            user_result = connection.execute(
                text(INSERT_MESSAGE_SQL),
                {
                    "room_id": payload.room_id,
                    "role": "user",
                    "message_order": user_message_order,
                    "content": payload.content,
                },
            )
            user_message_id = int(user_result.lastrowid)
            user_message = fetch_message_by_id(connection, user_message_id)

            assistant_reply = build_assistant_reply(payload.content, payload.assistant_mode)
            assistant_message_order = get_next_message_order(connection, payload.room_id)
            assistant_result = connection.execute(
                text(INSERT_MESSAGE_SQL),
                {
                    "room_id": payload.room_id,
                    "role": "assistant",
                    "message_order": assistant_message_order,
                    "content": assistant_reply,
                },
            )
            assistant_message_id = int(assistant_result.lastrowid)
            assistant_message = fetch_message_by_id(connection, assistant_message_id)

        response_payload = {
            "status": "ok",
            "message": "Chat completed successfully.",
            "room_id": payload.room_id,
            "user_message": serialize_message(user_message),
            "assistant_message": serialize_message(assistant_message),
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
            "Chat failed because of a database integrity rule.",
        )
    except (ValueError, SQLAlchemyError) as exc:
        return build_db_error_response(
            exc,
            "Chat failed. Make sure the rooms/messages tables exist and the db container is running.",
        )
    finally:
        if engine is not None:
            engine.dispose()
