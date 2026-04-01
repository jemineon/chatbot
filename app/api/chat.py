import os
from typing import Literal, Optional

from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.api.common import (
    db_error_response,
    duplicate_message_order_response,
    error_response,
    room_not_found_response,
    serialize_row,
    success_response,
)
from app.db.connection import db_transaction
from app.db.queries import (
    fetch_message_by_id,
    get_next_message_order,
    insert_message,
    list_recent_room_history,
    room_exists,
)
from app.llm import DEFAULT_GEMINI_HISTORY_LIMIT, generate_assistant_reply


router = APIRouter(tags=["Chat"])


class ChatRequest(BaseModel):
    room_id: int = Field(ge=1)
    content: str = Field(min_length=1)
    assistant_mode: Optional[Literal["gemini", "echo"]] = None


def build_assistant_reply(user_content: str, assistant_mode: str, history_rows: list[dict[str, object]]) -> str:
    if assistant_mode == "echo":
        return f"Echo: {user_content}"

    return generate_assistant_reply(history_rows)


def get_default_assistant_mode() -> str:
    assistant_mode = os.getenv("CHAT_ASSISTANT_MODE", "gemini")
    return assistant_mode if assistant_mode in {"gemini", "echo"} else "gemini"


@router.post("/chat")
def chat(payload: ChatRequest):
    try:
        with db_transaction() as connection:
            if not room_exists(connection, payload.room_id):
                return room_not_found_response(payload.room_id)

            user_message_id = insert_message(
                connection,
                payload.room_id,
                "user",
                get_next_message_order(connection, payload.room_id),
                payload.content,
            )
            user_message = fetch_message_by_id(connection, user_message_id)

            assistant_mode = payload.assistant_mode or get_default_assistant_mode()
            history_rows = list_recent_room_history(connection, payload.room_id, DEFAULT_GEMINI_HISTORY_LIMIT)
            assistant_reply = build_assistant_reply(payload.content, assistant_mode, history_rows)
            assistant_message_id = insert_message(
                connection,
                payload.room_id,
                "assistant",
                get_next_message_order(connection, payload.room_id),
                assistant_reply,
            )
            assistant_message = fetch_message_by_id(connection, assistant_message_id)

        return success_response(
            status.HTTP_201_CREATED,
            "Chat completed successfully.",
            room_id=payload.room_id,
            user_message=serialize_row(user_message),
            assistant_message=serialize_row(assistant_message),
        )
    except IntegrityError as exc:
        if "Duplicate entry" in str(getattr(exc, "orig", exc)):
            return duplicate_message_order_response()

        return db_error_response(
            exc,
            "Chat failed because of a database integrity rule.",
        )
    except (ValueError, SQLAlchemyError) as exc:
        return db_error_response(
            exc,
            "Chat failed. Make sure the rooms/messages tables exist and the db container is running.",
        )
    except RuntimeError as exc:
        return error_response(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            f"Gemini call failed: {exc}",
        )
