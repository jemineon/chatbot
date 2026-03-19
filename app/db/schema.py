from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, Text, func
from sqlalchemy.engine import Engine


metadata = MetaData()

messages = Table(
    "messages",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("room_id", Integer, nullable=False),
    Column("role", String(20), nullable=False),
    Column("message_order", Integer, nullable=False),
    Column("content", Text, nullable=False),
    Column("created_at", DateTime, nullable=False, server_default=func.now()),
)


def create_tables(engine: Engine) -> None:
    metadata.create_all(engine)
