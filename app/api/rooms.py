from fastapi import APIRouter, Path, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.common import db_error_response, error_response, serialize_row, success_response
from app.db.connection import db_connection, db_transaction
from app.db.queries import fetch_room_by_id, room_has_messages
from app.db.sql.rooms import (
    DELETE_ROOM_SQL,
    INSERT_ROOM_SQL,
    LIST_ROOMS_SQL,
)


router = APIRouter(tags=["Rooms"])


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


@router.post("/rooms")
def create_room(payload: RoomCreate):
    try:
        with db_transaction() as connection:
            result = connection.execute(
                text(INSERT_ROOM_SQL),
                {"name": payload.name},
            )
            room_id = int(result.lastrowid)
            row = fetch_room_by_id(connection, room_id)

        return success_response(
            status.HTTP_201_CREATED,
            "Room created successfully.",
            data=serialize_row(row),
        )
    except (ValueError, SQLAlchemyError) as exc:
        return db_error_response(
            exc,
            "Room create failed. Make sure the rooms table exists and the db container is running.",
        )


@router.get("/rooms")
def list_rooms():
    try:
        with db_connection() as connection:
            rows = connection.execute(text(LIST_ROOMS_SQL)).mappings().all()

        items = [serialize_row(row) for row in rows]
        return success_response(
            status.HTTP_200_OK,
            "Rooms fetched successfully.",
            count=len(items),
            items=items,
        )
    except (ValueError, SQLAlchemyError) as exc:
        return db_error_response(
            exc,
            "Room list query failed. Make sure the rooms table exists and the db container is running.",
        )


@router.get("/rooms/{room_id}")
def get_room(room_id: int = Path(ge=1)):
    try:
        with db_connection() as connection:
            row = fetch_room_by_id(connection, room_id)

        if row is None:
            return error_response(status.HTTP_404_NOT_FOUND, "Room not found.")

        return success_response(
            status.HTTP_200_OK,
            "Room fetched successfully.",
            data=serialize_row(row),
        )
    except (ValueError, SQLAlchemyError) as exc:
        return db_error_response(
            exc,
            "Room detail query failed. Make sure the rooms table exists and the db container is running.",
        )


@router.delete("/rooms/{room_id}")
def delete_room(room_id: int = Path(ge=1)):
    try:
        with db_transaction() as connection:
            room_row = fetch_room_by_id(connection, room_id)

            if room_row is None:
                return error_response(status.HTTP_404_NOT_FOUND, "Room not found.")

            if room_has_messages(connection, room_id):
                return error_response(
                    status.HTTP_409_CONFLICT,
                    "Room cannot be deleted because messages still exist in it. Delete the messages first.",
                )

            connection.execute(text(DELETE_ROOM_SQL), {"room_id": room_id})

        return success_response(
            status.HTTP_200_OK,
            "Room deleted successfully.",
            data=serialize_row(room_row),
        )
    except (ValueError, SQLAlchemyError) as exc:
        return db_error_response(
            exc,
            "Room delete failed. Make sure the rooms table exists and the db container is running.",
        )
