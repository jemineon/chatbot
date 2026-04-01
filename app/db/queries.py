from typing import Any, Mapping, Optional

from sqlalchemy import text

from app.db.sql.messages import (
    INSERT_MESSAGE_SQL,
    LIST_RECENT_MESSAGES_BY_ROOM_SQL,
    SELECT_MESSAGE_BY_ID_SQL,
    SELECT_NEXT_MESSAGE_ORDER_SQL,
)
from app.db.sql.rooms import (
    CHECK_ROOM_EXISTS_SQL,
    CHECK_ROOM_HAS_MESSAGES_SQL,
    SELECT_ROOM_BY_ID_SQL,
)


def fetch_room_by_id(connection: Any, room_id: int) -> Optional[Mapping[str, Any]]:
    return connection.execute(
        text(SELECT_ROOM_BY_ID_SQL),
        {"room_id": room_id},
    ).mappings().first()


def room_exists(connection: Any, room_id: int) -> bool:
    row = connection.execute(
        text(CHECK_ROOM_EXISTS_SQL),
        {"room_id": room_id},
    ).first()
    return row is not None


def room_has_messages(connection: Any, room_id: int) -> bool:
    row = connection.execute(
        text(CHECK_ROOM_HAS_MESSAGES_SQL),
        {"room_id": room_id},
    ).first()
    return row is not None


def fetch_message_by_id(connection: Any, message_id: int) -> Optional[Mapping[str, Any]]:
    return connection.execute(
        text(SELECT_MESSAGE_BY_ID_SQL),
        {"message_id": message_id},
    ).mappings().first()


def get_next_message_order(connection: Any, room_id: int) -> int:
    next_order = connection.execute(
        text(SELECT_NEXT_MESSAGE_ORDER_SQL),
        {"room_id": room_id},
    ).scalar()
    return int(next_order)


def insert_message(connection: Any, room_id: int, role: str, message_order: int, content: str) -> int:
    result = connection.execute(
        text(INSERT_MESSAGE_SQL),
        {
            "room_id": room_id,
            "role": role,
            "message_order": message_order,
            "content": content,
        },
    )
    return int(result.lastrowid)


def list_recent_room_history(connection: Any, room_id: int, history_limit: int) -> list[dict[str, Any]]:
    rows = connection.execute(
        text(LIST_RECENT_MESSAGES_BY_ROOM_SQL),
        {"room_id": room_id, "history_limit": history_limit},
    ).mappings().all()
    return list(reversed([dict(row) for row in rows]))
