import json
import time
import unittest
from typing import Any, Dict, Optional, Tuple
from urllib import error, request

from sqlalchemy import text

from app.db.connection import create_db_engine
from app.db.schema import create_tables


class MessagesApiIntegrationTestCase(unittest.TestCase):
    base_url = "http://127.0.0.1:8000"

    @staticmethod
    def debug(message: str) -> None:
        print(f"[DEBUG] {message}", flush=True)

    @classmethod
    def setUpClass(cls) -> None:
        cls.debug("Creating SQLAlchemy engine for API integration test setup.")
        cls.engine = create_db_engine()
        cls.debug("Ensuring the messages table exists before calling the API.")
        create_tables(cls.engine)
        cls.wait_for_api()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.debug("Disposing SQLAlchemy engine.")
        cls.engine.dispose()

    @classmethod
    def wait_for_api(cls, timeout_seconds: int = 10) -> None:
        cls.debug("Waiting for FastAPI server to respond on /api/v1/health.")
        deadline = time.time() + timeout_seconds
        last_error: Optional[str] = None

        while time.time() < deadline:
            try:
                status_code, body = cls.request_json("GET", "/api/v1/health")
                if status_code == 200 and body.get("status") == "ok":
                    cls.debug(f"FastAPI health check succeeded -> {body}")
                    return
                last_error = f"Unexpected health response: status={status_code}, body={body}"
            except Exception as exc:
                last_error = str(exc)

            time.sleep(1)

        raise AssertionError(
            "FastAPI server did not become ready in time. "
            f"Last error: {last_error}"
        )

    @classmethod
    def request_json(
        cls,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, Dict[str, Any]]:
        url = f"{cls.base_url}{path}"
        data = None
        headers = {"Content-Type": "application/json"}

        if payload is not None:
            data = json.dumps(payload).encode("utf-8")

        req = request.Request(url=url, data=data, headers=headers, method=method)

        try:
            with request.urlopen(req) as response:
                status_code = response.getcode()
                raw_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            status_code = exc.code
            raw_body = exc.read().decode("utf-8")
        except error.URLError as exc:
            raise AssertionError(f"API request failed: {method} {url} -> {exc.reason}") from exc

        try:
            body = json.loads(raw_body) if raw_body else {}
        except json.JSONDecodeError as exc:
            raise AssertionError(
                f"API returned non-JSON response: {method} {url} -> {raw_body}"
            ) from exc

        return status_code, body

    def setUp(self) -> None:
        self.debug("Cleaning rooms/messages tables so the API test starts from a known state.")
        with self.engine.begin() as connection:
            connection.execute(text("DELETE FROM messages"))
            connection.execute(text("DELETE FROM rooms"))

    def create_room_via_api(self, name: str = "test room") -> int:
        status_code, body = self.request_json(
            "POST",
            "/api/v1/rooms",
            payload={"name": name},
        )
        self.debug(f"Room create response -> status={status_code}, body={body}")
        self.assertEqual(status_code, 201, f"Expected HTTP 201 for room create, got {status_code}. Body: {body}")
        return int(body["data"]["id"])

    def test_health_db_endpoint(self) -> None:
        self.debug("Checking GET /api/v1/health/db before running CRUD flow.")
        status_code, body = self.request_json("GET", "/api/v1/health/db")
        self.debug(f"/api/v1/health/db response -> status={status_code}, body={body}")

        self.assertEqual(status_code, 200, f"Expected HTTP 200, got {status_code}. Body: {body}")
        self.assertEqual(body["status"], "ok", f"Expected status='ok', got {body}")
        self.assertEqual(body["ping"], 1, f"Expected ping=1, got {body}")

    def test_rooms_api_create_and_list(self) -> None:
        room_id = self.create_room_via_api(name="api room")

        status_code, body = self.request_json("GET", "/api/v1/rooms")
        self.debug(f"Room list response -> status={status_code}, body={body}")

        self.assertEqual(status_code, 200, f"Expected HTTP 200 for room list, got {status_code}. Body: {body}")
        self.assertEqual(body["count"], 1, f"Expected one room in list, got {body}")
        self.assertEqual(body["items"][0]["id"], room_id, f"Expected listed room id={room_id}, got {body}")
        self.assertEqual(body["items"][0]["name"], "api room", f"Expected room name='api room', got {body}")

    def test_room_detail_api(self) -> None:
        room_id = self.create_room_via_api(name="detail room")

        status_code, body = self.request_json("GET", f"/api/v1/rooms/{room_id}")
        self.debug(f"Room detail response -> status={status_code}, body={body}")

        self.assertEqual(status_code, 200, f"Expected HTTP 200 for room detail, got {status_code}. Body: {body}")
        self.assertEqual(body["data"]["id"], room_id, f"Expected room id={room_id}, got {body}")
        self.assertEqual(body["data"]["name"], "detail room", f"Expected room name='detail room', got {body}")

    def test_room_delete_api(self) -> None:
        room_id = self.create_room_via_api(name="delete room")

        delete_status, delete_body = self.request_json("DELETE", f"/api/v1/rooms/{room_id}")
        self.debug(f"Room delete response -> status={delete_status}, body={delete_body}")

        self.assertEqual(delete_status, 200, f"Expected HTTP 200 for room delete, got {delete_status}. Body: {delete_body}")
        self.assertEqual(delete_body["data"]["id"], room_id, f"Expected deleted room id={room_id}, got {delete_body}")

        detail_status, detail_body = self.request_json("GET", f"/api/v1/rooms/{room_id}")
        self.debug(f"Room detail after delete -> status={detail_status}, body={detail_body}")

        self.assertEqual(detail_status, 404, f"Expected HTTP 404 after room delete, got {detail_status}. Body: {detail_body}")
        self.assertEqual(detail_body["message"], "Room not found.", f"Unexpected room detail body after delete: {detail_body}")

    def test_room_delete_is_blocked_when_messages_exist(self) -> None:
        room_id = self.create_room_via_api(name="blocked delete room")

        create_status, create_body = self.request_json(
            "POST",
            "/api/v1/messages",
            payload={
                "room_id": room_id,
                "role": "user",
                "content": "message keeps room alive",
            },
        )
        self.debug(f"Message create before room delete -> status={create_status}, body={create_body}")
        self.assertEqual(create_status, 201, f"Expected message create to succeed, got {create_status}. Body: {create_body}")

        delete_status, delete_body = self.request_json("DELETE", f"/api/v1/rooms/{room_id}")
        self.debug(f"Blocked room delete response -> status={delete_status}, body={delete_body}")

        self.assertEqual(delete_status, 409, f"Expected HTTP 409 when room still has messages, got {delete_status}. Body: {delete_body}")
        self.assertEqual(
            delete_body["message"],
            "Room cannot be deleted because messages still exist in it. Delete the messages first.",
            f"Unexpected blocked delete message: {delete_body}",
        )

    def test_chat_api_creates_user_and_assistant_messages(self) -> None:
        room_id = self.create_room_via_api(name="chat room")

        chat_status, chat_body = self.request_json(
            "POST",
            "/api/v1/chat",
            payload={
                "room_id": room_id,
                "content": "hello chat api",
            },
        )
        self.debug(f"Chat response -> status={chat_status}, body={chat_body}")

        self.assertEqual(chat_status, 201, f"Expected HTTP 201 for chat, got {chat_status}. Body: {chat_body}")
        self.assertEqual(chat_body["status"], "ok", f"Unexpected chat body: {chat_body}")
        self.assertEqual(chat_body["room_id"], room_id, f"Expected room_id={room_id}, got {chat_body}")
        self.assertEqual(chat_body["user_message"]["role"], "user", f"Expected user role, got {chat_body}")
        self.assertEqual(chat_body["user_message"]["message_order"], 1, f"Expected user message_order=1, got {chat_body}")
        self.assertEqual(chat_body["user_message"]["content"], "hello chat api", f"Unexpected user message body: {chat_body}")
        self.assertEqual(chat_body["assistant_message"]["role"], "assistant", f"Expected assistant role, got {chat_body}")
        self.assertEqual(chat_body["assistant_message"]["message_order"], 2, f"Expected assistant message_order=2, got {chat_body}")
        self.assertEqual(chat_body["assistant_message"]["content"], "Echo: hello chat api", f"Unexpected assistant reply: {chat_body}")

        list_status, list_body = self.request_json("GET", f"/api/v1/messages?room_id={room_id}")
        self.debug(f"Chat room messages response -> status={list_status}, body={list_body}")

        self.assertEqual(list_status, 200, f"Expected HTTP 200 for room messages list, got {list_status}. Body: {list_body}")
        self.assertEqual(list_body["count"], 2, f"Expected two stored messages after chat, got {list_body}")

    def test_messages_api_crud_flow(self) -> None:
        room_id = self.create_room_via_api()
        self.debug("Step 1: POST /api/v1/messages")
        create_status, create_body = self.request_json(
            "POST",
            "/api/v1/messages",
            payload={
                "room_id": room_id,
                "role": "user",
                "content": "hello from api test",
            },
        )
        self.debug(f"Create response -> status={create_status}, body={create_body}")

        self.assertEqual(
            create_status,
            201,
            f"Expected HTTP 201 for create, got {create_status}. Body: {create_body}",
        )
        self.assertEqual(create_body["status"], "ok", f"Create API returned unexpected body: {create_body}")

        created_message = create_body["data"]
        message_id = created_message["id"]

        self.assertEqual(created_message["room_id"], room_id, f"Expected room_id={room_id}, got {created_message}")
        self.assertEqual(created_message["role"], "user", f"Expected role='user', got {created_message}")
        self.assertEqual(
            created_message["message_order"],
            1,
            f"Expected auto-assigned message_order=1, got {created_message}",
        )
        self.assertEqual(
            created_message["content"],
            "hello from api test",
            f"Expected inserted content to match, got {created_message}",
        )
        self.assertIsNotNone(
            created_message["created_at"],
            f"Expected created_at to be present, got {created_message}",
        )

        self.debug("Step 2: GET /api/v1/messages")
        list_status, list_body = self.request_json("GET", "/api/v1/messages")
        self.debug(f"List response -> status={list_status}, body={list_body}")

        self.assertEqual(list_status, 200, f"Expected HTTP 200 for list, got {list_status}. Body: {list_body}")
        self.assertEqual(list_body["count"], 1, f"Expected one message in list, got {list_body}")
        self.assertEqual(
            list_body["items"][0]["id"],
            message_id,
            f"Expected listed id={message_id}, got {list_body}",
        )

        self.debug("Step 3: GET /api/v1/messages/{message_id}")
        detail_status, detail_body = self.request_json("GET", f"/api/v1/messages/{message_id}")
        self.debug(f"Detail response -> status={detail_status}, body={detail_body}")

        self.assertEqual(
            detail_status,
            200,
            f"Expected HTTP 200 for detail, got {detail_status}. Body: {detail_body}",
        )
        self.assertEqual(
            detail_body["data"]["id"],
            message_id,
            f"Expected detail id={message_id}, got {detail_body}",
        )

        self.debug("Step 4: PUT /api/v1/messages/{message_id}")
        update_status, update_body = self.request_json(
            "PUT",
            f"/api/v1/messages/{message_id}",
            payload={
                "room_id": room_id,
                "role": "assistant",
                "content": "updated from api test",
            },
        )
        self.debug(f"Update response -> status={update_status}, body={update_body}")

        self.assertEqual(
            update_status,
            200,
            f"Expected HTTP 200 for update, got {update_status}. Body: {update_body}",
        )
        self.assertEqual(
            update_body["data"]["role"],
            "assistant",
            f"Expected role='assistant', got {update_body}",
        )
        self.assertEqual(
            update_body["data"]["message_order"],
            1,
            f"Expected message_order to stay 1 in the same room, got {update_body}",
        )
        self.assertEqual(
            update_body["data"]["content"],
            "updated from api test",
            f"Expected updated content to match, got {update_body}",
        )

        self.debug("Step 5: DELETE /api/v1/messages/{message_id}")
        delete_status, delete_body = self.request_json("DELETE", f"/api/v1/messages/{message_id}")
        self.debug(f"Delete response -> status={delete_status}, body={delete_body}")

        self.assertEqual(
            delete_status,
            200,
            f"Expected HTTP 200 for delete, got {delete_status}. Body: {delete_body}",
        )
        self.assertEqual(
            delete_body["data"]["id"],
            message_id,
            f"Expected deleted id={message_id}, got {delete_body}",
        )

        self.debug("Step 6: GET /api/v1/messages/{message_id} after delete")
        missing_status, missing_body = self.request_json("GET", f"/api/v1/messages/{message_id}")
        self.debug(f"Missing detail response -> status={missing_status}, body={missing_body}")

        self.assertEqual(
            missing_status,
            404,
            f"Expected HTTP 404 after delete, got {missing_status}. Body: {missing_body}",
        )
        self.assertEqual(
            missing_body["message"],
            "Message not found.",
            f"Expected 'Message not found.' after delete, got {missing_body}",
        )

    def test_message_order_is_auto_incremented_in_same_room(self) -> None:
        room_id = self.create_room_via_api(name="auto order room")

        first_status, first_body = self.request_json(
            "POST",
            "/api/v1/messages",
            payload={
                "room_id": room_id,
                "role": "user",
                "content": "first message",
            },
        )
        second_status, second_body = self.request_json(
            "POST",
            "/api/v1/messages",
            payload={
                "room_id": room_id,
                "role": "assistant",
                "content": "second message",
            },
        )

        self.debug(f"First create response -> status={first_status}, body={first_body}")
        self.debug(f"Second create response -> status={second_status}, body={second_body}")

        self.assertEqual(first_status, 201, f"Expected first create to succeed, got {first_status}. Body: {first_body}")
        self.assertEqual(second_status, 201, f"Expected second create to succeed, got {second_status}. Body: {second_body}")
        self.assertEqual(first_body["data"]["message_order"], 1, f"Expected first message_order=1, got {first_body}")
        self.assertEqual(second_body["data"]["message_order"], 2, f"Expected second message_order=2, got {second_body}")

    def test_message_order_starts_from_one_in_each_room(self) -> None:
        room_one_id = self.create_room_via_api(name="room one")
        room_two_id = self.create_room_via_api(name="room two")

        first_status, first_body = self.request_json(
            "POST",
            "/api/v1/messages",
            payload={
                "room_id": room_one_id,
                "role": "user",
                "content": "room one message",
            },
        )
        second_status, second_body = self.request_json(
            "POST",
            "/api/v1/messages",
            payload={
                "room_id": room_two_id,
                "role": "assistant",
                "content": "room two message",
            },
        )

        self.debug(f"Room one create response -> status={first_status}, body={first_body}")
        self.debug(f"Room two create response -> status={second_status}, body={second_body}")

        self.assertEqual(first_status, 201, f"Expected room one message create to succeed, got {first_status}.")
        self.assertEqual(second_status, 201, f"Expected room two message create to succeed, got {second_status}.")
        self.assertEqual(first_body["data"]["message_order"], 1, f"Expected room one first message_order=1, got {first_body}")
        self.assertEqual(second_body["data"]["message_order"], 1, f"Expected room two first message_order=1, got {second_body}")

    def test_message_order_is_reassigned_when_room_changes(self) -> None:
        source_room_id = self.create_room_via_api(name="source room")
        target_room_id = self.create_room_via_api(name="target room")

        first_source_status, first_source_body = self.request_json(
            "POST",
            "/api/v1/messages",
            payload={
                "room_id": source_room_id,
                "role": "user",
                "content": "source message",
            },
        )
        first_target_status, first_target_body = self.request_json(
            "POST",
            "/api/v1/messages",
            payload={
                "room_id": target_room_id,
                "role": "assistant",
                "content": "target message",
            },
        )

        message_id = first_source_body["data"]["id"]

        move_status, move_body = self.request_json(
            "PUT",
            f"/api/v1/messages/{message_id}",
            payload={
                "room_id": target_room_id,
                "role": "user",
                "content": "moved message",
            },
        )

        self.debug(f"Source create response -> status={first_source_status}, body={first_source_body}")
        self.debug(f"Target create response -> status={first_target_status}, body={first_target_body}")
        self.debug(f"Move response -> status={move_status}, body={move_body}")

        self.assertEqual(move_status, 200, f"Expected move update to succeed, got {move_status}. Body: {move_body}")
        self.assertEqual(move_body["data"]["room_id"], target_room_id, f"Expected room_id={target_room_id}, got {move_body}")
        self.assertEqual(move_body["data"]["message_order"], 2, f"Expected moved message_order=2 in target room, got {move_body}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
