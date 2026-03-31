import json
import os
from typing import Any, Dict, Optional, Tuple
from urllib import error, request


DEFAULT_API_BASE_URL = os.getenv("CHAT_API_BASE_URL", "http://127.0.0.1:8000/api/v1")


def request_json(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Dict[str, Any]]:
    url = f"{DEFAULT_API_BASE_URL}{path}"
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
        raise RuntimeError(f"API request failed: {method} {url} -> {exc.reason}") from exc

    try:
        body = json.loads(raw_body) if raw_body else {}
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"API returned non-JSON response: {method} {url} -> {raw_body}") from exc

    return status_code, body


def create_room(room_name: str) -> int:
    status_code, body = request_json("POST", "/rooms", {"name": room_name})

    if status_code != 201:
        raise RuntimeError(f"Room creation failed: {body}")

    return int(body["data"]["id"])


def print_history(room_id: int) -> None:
    status_code, body = request_json("GET", f"/messages?room_id={room_id}")

    if status_code != 200:
        print(f"[ERROR] Failed to fetch history: {body}")
        return

    print("\n[HISTORY]")
    for item in body.get("items", []):
        print(f"{item['message_order']}. {item['role']}: {item['content']}")
    print()


def chat_loop(room_id: int) -> None:
    print(f"[INFO] Room id={room_id}")
    print("[INFO] Type a message and press Enter.")
    print("[INFO] Commands: /history, /exit\n")

    while True:
        user_input = input("you> ").strip()

        if not user_input:
            continue

        if user_input == "/exit":
            print("bye")
            break

        if user_input == "/history":
            print_history(room_id)
            continue

        status_code, body = request_json(
            "POST",
            "/chat",
            {"room_id": room_id, "content": user_input},
        )

        if status_code != 201:
            print(f"[ERROR] Chat request failed: {body}")
            continue

        assistant_message = body["assistant_message"]["content"]
        print(f"assistant> {assistant_message}")


def main() -> None:
    room_name = input("room name (blank for 'CLI Chat Room'): ").strip() or "CLI Chat Room"
    room_id = create_room(room_name)
    chat_loop(room_id)


if __name__ == "__main__":
    main()
