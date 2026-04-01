from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, Path, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.api.common import (
    db_error_response,
    duplicate_message_order_response,
    error_response,
    room_not_found_response,
    serialize_row,
    success_response,
)
from app.db.connection import db_connection, db_transaction
from app.db.queries import fetch_message_by_id, get_next_message_order, insert_message, room_exists
from app.db.sql.messages import (
    DELETE_MESSAGE_SQL,
    LIST_ALL_MESSAGES_SQL,
    LIST_MESSAGES_BY_ROOM_SQL,
    UPDATE_MESSAGE_SQL,
)


router = APIRouter(tags=["Messages"])


class MessageCreate(BaseModel):
    room_id: int = Field(ge=1)
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1)


class MessageUpdate(BaseModel):
    room_id: int = Field(ge=1)
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1)


def serialize_message(row: Any) -> Optional[dict[str, Any]]:
    return serialize_row(row)


@router.post("/messages")
def create_message(payload: MessageCreate):
    try:
        with db_transaction() as connection:
            if not room_exists(connection, payload.room_id):
                return room_not_found_response(payload.room_id)

            message_id = insert_message(
                connection,
                payload.room_id,
                payload.role,
                get_next_message_order(connection, payload.room_id),
                payload.content,
            )
            row = fetch_message_by_id(connection, message_id)

        return success_response(
            status.HTTP_201_CREATED,
            "Message created successfully.",
            data=serialize_message(row),
        )
    except IntegrityError as exc:
        if "Duplicate entry" in str(getattr(exc, "orig", exc)):
            return duplicate_message_order_response()

        return db_error_response(
            exc,
            "Message create failed because of a database integrity rule.",
        )
    except (ValueError, SQLAlchemyError) as exc:
        return db_error_response(
            exc,
            "Message create failed. Make sure the rooms/messages tables exist and the db container is running.",
        )


@router.get("/messages")
def list_messages(room_id: Optional[int] = Query(default=None, ge=1)):
    try:
        query = LIST_MESSAGES_BY_ROOM_SQL if room_id is not None else LIST_ALL_MESSAGES_SQL
        params: Dict[str, Any] = {"room_id": room_id} if room_id is not None else {}

        with db_connection() as connection:
            rows = connection.execute(text(query), params).mappings().all()

        items = [serialize_message(row) for row in rows]
        return success_response(
            status.HTTP_200_OK,
            "Messages fetched successfully.",
            count=len(items),
            items=items,
        )
    except (ValueError, SQLAlchemyError) as exc:
        return db_error_response(
            exc,
            "Message list query failed. Make sure the messages table exists and the db container is running.",
        )


@router.get("/messages/{message_id}")
def get_message(message_id: int = Path(ge=1)):
    try:
        with db_connection() as connection:
            row = fetch_message_by_id(connection, message_id)

        if row is None:
            return error_response(status.HTTP_404_NOT_FOUND, "Message not found.")

        return success_response(
            status.HTTP_200_OK,
            "Message fetched successfully.",
            data=serialize_message(row),
        )
    except (ValueError, SQLAlchemyError) as exc:
        return db_error_response(
            exc,
            "Message detail query failed. Make sure the messages table exists and the db container is running.",
        )


@router.put("/messages/{message_id}")
def update_message(message_id: int = Path(ge=1), payload: MessageUpdate = ...):
    try:
        with db_transaction() as connection:
            existing_message = fetch_message_by_id(connection, message_id)

            if existing_message is None:
                return error_response(status.HTTP_404_NOT_FOUND, "Message not found.")

            if not room_exists(connection, payload.room_id):
                return room_not_found_response(payload.room_id)

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
                return error_response(status.HTTP_404_NOT_FOUND, "Message not found.")

            row = fetch_message_by_id(connection, message_id)

        return success_response(
            status.HTTP_200_OK,
            "Message updated successfully.",
            data=serialize_message(row),
        )
    except IntegrityError as exc:
        if "Duplicate entry" in str(getattr(exc, "orig", exc)):
            return duplicate_message_order_response()

        return db_error_response(
            exc,
            "Message update failed because of a database integrity rule.",
        )
    except (ValueError, SQLAlchemyError) as exc:
        return db_error_response(
            exc,
            "Message update failed. Make sure the rooms/messages tables exist and the db container is running.",
        )


@router.delete("/messages/{message_id}")
def delete_message(message_id: int = Path(ge=1)):
    try:
        with db_transaction() as connection:
            row = fetch_message_by_id(connection, message_id)

            if row is None:
                return error_response(status.HTTP_404_NOT_FOUND, "Message not found.")

            connection.execute(text(DELETE_MESSAGE_SQL), {"message_id": message_id})

        return success_response(
            status.HTTP_200_OK,
            "Message deleted successfully.",
            data=serialize_message(row),
        )
    except (ValueError, SQLAlchemyError) as exc:
        return db_error_response(
            exc,
            "Message delete failed. Make sure the messages table exists and the db container is running.",
        )
