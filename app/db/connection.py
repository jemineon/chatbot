import os
from typing import Any, Dict, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


def get_database_url() -> str:
    host = os.getenv("MYSQL_HOST", "")
    port = os.getenv("MYSQL_PORT", "")
    user = os.getenv("MYSQL_USER", "")
    password = os.getenv("MYSQL_PASSWORD", "")
    database = os.getenv("MYSQL_DATABASE", "")

    required_env = {
        "MYSQL_HOST": host,
        "MYSQL_PORT": port,
        "MYSQL_USER": user,
        "MYSQL_PASSWORD": password,
        "MYSQL_DATABASE": database,
    }
    missing = [name for name, value in required_env.items() if not value]

    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Missing required environment variables: {missing_text}")

    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"


def create_db_engine() -> Engine:
    # pool_pre_ping helps detect stale connections in a simple way.
    return create_engine(get_database_url(), pool_pre_ping=True)


def check_db_connection() -> Dict[str, Any]:
    host = os.getenv("MYSQL_HOST", "")
    database = os.getenv("MYSQL_DATABASE", "")
    engine: Optional[Engine] = None

    try:
        engine = create_db_engine()

        with engine.connect() as connection:
            ping = connection.execute(text("SELECT 1 AS ping")).scalar()

        return {
            "status": "ok",
            "message": "MySQL connection succeeded.",
            "host": host,
            "database": database,
            "ping": ping,
        }
    except ValueError as exc:
        return {
            "status": "error",
            "message": "Database settings are missing. Check your .env file and Docker Compose environment variables.",
            "host": host,
            "database": database,
            "error": str(exc),
        }
    except SQLAlchemyError as exc:
        root_error = str(getattr(exc, "orig", exc))

        return {
            "status": "error",
            "message": "MySQL connection failed. Make sure the db container is running and the MYSQL_* values are correct.",
            "host": host,
            "database": database,
            "error": root_error,
        }
    finally:
        if engine is not None:
            engine.dispose()
