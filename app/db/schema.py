from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.engine import Engine


metadata = MetaData()

rooms = Table(
    "rooms",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(100), nullable=False),
    Column("created_at", DateTime, nullable=False, server_default=func.now()),
)

messages = Table(
    "messages",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("room_id", Integer, ForeignKey("rooms.id"), nullable=False),
    Column("role", String(20), nullable=False),
    Column("message_order", Integer, nullable=False),
    Column("content", Text, nullable=False),
    Column("created_at", DateTime, nullable=False, server_default=func.now()),
    UniqueConstraint("room_id", "message_order", name="uq_messages_room_id_message_order"),
)


def create_tables(engine: Engine) -> None:
    metadata.create_all(engine)


def drop_tables(engine: Engine) -> None:
    metadata.drop_all(engine)
