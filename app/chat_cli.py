import json
import os
from typing import Any, Dict, List, Optional, Tuple
from urllib import error, request


DEFAULT_API_BASE_URL = os.getenv("CHAT_API_BASE_URL", "http://127.0.0.1:8000/api/v1")
DEFAULT_ROOM_NAME = "CLI Chat Room"


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


def require_success(status_code: int, expected_status: int, body: Dict[str, Any], context: str) -> None:
    if status_code != expected_status:
        raise RuntimeError(f"{context} failed: {body}")


def create_room(room_name: str) -> int:
    status_code, body = request_json("POST", "/rooms", {"name": room_name})
    require_success(status_code, 201, body, "Room creation")
    return int(body["data"]["id"])


def list_rooms() -> List[Dict[str, Any]]:
    status_code, body = request_json("GET", "/rooms")
    require_success(status_code, 200, body, "Room list")
    return body.get("items", [])


def prompt_room_name(prompt: str) -> str:
    return input(prompt).strip() or DEFAULT_ROOM_NAME


def print_info(message: str) -> None:
    print(f"[INFO] {message}")


def print_error(message: str) -> None:
    print(f"[ERROR] {message}")


def print_rooms(rooms: List[Dict[str, Any]]) -> None:
    if not rooms:
        print("\n[ROOMS] 아직 room이 없습니다.\n")
        return

    print("\n[ROOMS]")
    for index, room in enumerate(rooms, start=1):
        print(f"{index}. #{room['id']} {room['name']}")
    print()


def print_history(room_id: int) -> None:
    status_code, body = request_json("GET", f"/messages?room_id={room_id}")

    if status_code != 200:
        print_error(f"Failed to fetch history: {body}")
        return

    print("\n[HISTORY]")
    for item in body.get("items", []):
        print(f"{item['message_order']}. {item['role']}: {item['content']}")
    print()


def create_room_from_prompt(prompt: str) -> Tuple[int, str]:
    room_name = prompt_room_name(prompt)
    room_id = create_room(room_name)
    return room_id, room_name


def choose_room() -> Tuple[int, str]:
    rooms = list_rooms()

    if not rooms:
        return create_room_from_prompt("room name (blank for 'CLI Chat Room'): ")

    print_rooms(rooms)
    print_info("번호를 입력하면 기존 room으로 들어갑니다.")
    print_info("n 을 입력하면 새 room을 만듭니다.\n")

    while True:
        user_input = input("select room> ").strip().lower()

        if user_input in {"", "n", "new"}:
            return create_room_from_prompt("new room name (blank for 'CLI Chat Room'): ")

        if user_input.isdigit():
            index = int(user_input) - 1

            if 0 <= index < len(rooms):
                room = rooms[index]
                return int(room["id"]), str(room["name"])

        print_error("올바른 room 번호를 입력하거나 n 을 입력하세요.")


def switch_room() -> Tuple[int, str]:
    print()
    print_info("room 전환")
    return choose_room()

# chat loop ui
def chat_loop(room_id: int, room_name: str) -> None:
    print_info(f"Room id={room_id} / name={room_name}")
    print_info("Type a message and press Enter.")
    print_info("Commands: /history, /rooms, /switch, /exit\n")
    print_history(room_id)

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

        if user_input == "/rooms":
            print_rooms(list_rooms())
            continue

        if user_input == "/switch":
            room_id, room_name = switch_room()
            print_info(f"Room id={room_id} / name={room_name}")
            print_history(room_id)
            continue

        status_code, body = request_json(
            "POST",
            "/chat",
            {"room_id": room_id, "content": user_input},
        )

        if status_code != 201:
            print_error(f"Chat request failed: {body}")
            continue

        assistant_message = body["assistant_message"]["content"]
        print(f"assistant> {assistant_message}")


def main() -> None:
    room_id, room_name = choose_room()
    chat_loop(room_id, room_name)


if __name__ == "__main__":
    main()
