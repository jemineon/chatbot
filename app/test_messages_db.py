import unittest

from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError

from app.db.connection import create_db_engine
from app.db.schema import create_tables, drop_tables, messages, rooms


class MessagesCrudDbTestCase(unittest.TestCase):
    @staticmethod
    def debug(message: str) -> None:
        print(f"[DEBUG] {message}", flush=True)

    @classmethod
    def setUpClass(cls) -> None:
        cls.debug("Creating SQLAlchemy engine for MySQL test database.")
        cls.engine = create_db_engine()
        cls.debug("Recreating rooms/messages tables so constraint tests start from the latest schema.")
        drop_tables(cls.engine)
        create_tables(cls.engine)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.debug("Disposing SQLAlchemy engine.")
        cls.engine.dispose()

    def setUp(self) -> None:
        self.debug("Cleaning rooms/messages tables so each test starts from a known state.")
        with self.engine.begin() as connection:
            connection.execute(delete(messages))
            connection.execute(delete(rooms))

    def create_room(self, name: str = "test room") -> int:
        with self.engine.begin() as connection:
            result = connection.execute(insert(rooms).values(name=name))
            return int(result.inserted_primary_key[0])

    def fetch_message(self, message_id: int):
        with self.engine.connect() as connection:
            return connection.execute(
                select(messages).where(messages.c.id == message_id)
            ).mappings().first()

    def test_messages_crud_flow(self) -> None:
        room_id = self.create_room()
        self.debug("Step 1: inserting a sample message row.")
        with self.engine.begin() as connection:
            insert_result = connection.execute(
                insert(messages).values(
                    room_id=room_id,
                    role="user",
                    message_order=1,
                    content="first message",
                )
            )
            message_id = int(insert_result.inserted_primary_key[0])
        self.debug(f"Inserted message id={message_id}.")

        created_message = self.fetch_message(message_id)
        self.debug(f"Step 2: fetched created row -> {dict(created_message) if created_message else None}")

        self.assertIsNotNone(created_message, "Create check failed: inserted row could not be read back.")
        self.assertEqual(created_message["room_id"], room_id, f"Expected room_id={room_id}, got {created_message['room_id']}.")
        self.assertEqual(created_message["role"], "user", f"Expected role='user', got {created_message['role']}.")
        self.assertEqual(
            created_message["message_order"],
            1,
            f"Expected message_order=1, got {created_message['message_order']}.",
        )
        self.assertEqual(
            created_message["content"],
            "first message",
            f"Expected content='first message', got {created_message['content']}.",
        )
        self.assertIsNotNone(created_message["created_at"], "Expected created_at to be automatically set.")

        self.debug("Step 3: updating the same row.")
        with self.engine.begin() as connection:
            connection.execute(
                update(messages)
                .where(messages.c.id == message_id)
                .values(
                    room_id=room_id,
                    role="assistant",
                    message_order=2,
                    content="updated message",
                )
            )

        updated_message = self.fetch_message(message_id)
        self.debug(f"Step 4: fetched updated row -> {dict(updated_message) if updated_message else None}")

        self.assertIsNotNone(updated_message, "Update check failed: updated row could not be read back.")
        self.assertEqual(
            updated_message["role"],
            "assistant",
            f"Expected role='assistant', got {updated_message['role']}.",
        )
        self.assertEqual(
            updated_message["message_order"],
            2,
            f"Expected message_order=2, got {updated_message['message_order']}.",
        )
        self.assertEqual(
            updated_message["content"],
            "updated message",
            f"Expected content='updated message', got {updated_message['content']}.",
        )

        self.debug("Step 5: deleting the row.")
        with self.engine.begin() as connection:
            connection.execute(delete(messages).where(messages.c.id == message_id))

        deleted_message = self.fetch_message(message_id)
        self.debug(f"Step 6: fetched row after delete -> {deleted_message}")

        self.assertIsNone(deleted_message, "Delete check failed: row still exists after delete.")

    def test_duplicate_message_order_is_blocked_in_same_room(self) -> None:
        room_id = self.create_room()
        self.debug("Creating the first message with message_order=1.")

        with self.engine.begin() as connection:
            connection.execute(
                insert(messages).values(
                    room_id=room_id,
                    role="user",
                    message_order=1,
                    content="first",
                )
            )

        self.debug("Trying to insert another message with the same room_id and message_order.")
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(
                    insert(messages).values(
                        room_id=room_id,
                        role="assistant",
                        message_order=1,
                        content="duplicate",
                    )
                )

    def test_same_message_order_is_allowed_in_different_rooms(self) -> None:
        room_one_id = self.create_room(name="room one")
        room_two_id = self.create_room(name="room two")
        self.debug("Inserting message_order=1 into two different rooms.")

        with self.engine.begin() as connection:
            connection.execute(
                insert(messages).values(
                    room_id=room_one_id,
                    role="user",
                    message_order=1,
                    content="room one message",
                )
            )
            connection.execute(
                insert(messages).values(
                    room_id=room_two_id,
                    role="assistant",
                    message_order=1,
                    content="room two message",
                )
            )

        with self.engine.connect() as connection:
            rows = connection.execute(select(messages).order_by(messages.c.id)).mappings().all()

        self.assertEqual(len(rows), 2, f"Expected two messages across different rooms, got {rows}")
        self.assertEqual(rows[0]["room_id"], room_one_id, f"Unexpected first row: {rows[0]}")
        self.assertEqual(rows[1]["room_id"], room_two_id, f"Unexpected second row: {rows[1]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
