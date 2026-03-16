from typing import Any, Dict, Optional

import pymysql
from pymysql.connections import Connection

from app.core.config import settings


def create_db_connection() -> Connection:
    # We keep the connection layer simple so beginners can verify MySQL first
    # and add SQLAlchemy or an ORM later.
    return pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
        connect_timeout=5,
        cursorclass=pymysql.cursors.DictCursor,
    )


def check_db_connection() -> Dict[str, Any]:
    connection: Optional[Connection] = None

    try:
        connection = create_db_connection()

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 AS ping")
            result = cursor.fetchone()

        return {
            "status": "ok",
            "message": "MySQL connection succeeded.",
            "database": settings.mysql_database,
            "host": settings.mysql_host,
            "ping": result["ping"] if result else None,
        }
    except pymysql.MySQLError as exc:
        return {
            "status": "error",
            "message": "MySQL connection failed.",
            "database": settings.mysql_database,
            "host": settings.mysql_host,
            "error": str(exc),
        }
    finally:
        if connection is not None:
            connection.close()
