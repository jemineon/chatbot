from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db.sql.schema import (
    CREATE_MESSAGES_TABLE_SQL,
    CREATE_ROOMS_TABLE_SQL,
    DROP_MESSAGES_TABLE_SQL,
    DROP_ROOMS_TABLE_SQL,
)


def create_tables(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text(CREATE_ROOMS_TABLE_SQL))
        connection.execute(text(CREATE_MESSAGES_TABLE_SQL))


def drop_tables(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text(DROP_MESSAGES_TABLE_SQL))
        connection.execute(text(DROP_ROOMS_TABLE_SQL))
