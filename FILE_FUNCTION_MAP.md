# 프로젝트 파일별 함수 역할 정리

이 문서는 현재 코드 기준으로 각 파일에 있는 함수와 클래스의 역할을 빠르게 파악할 수 있도록 정리한 자료입니다.

## `app/main.py`

- `read_frontend()`: 루트 경로(`/`)에서 `frontend.html` 파일을 반환합니다. 브라우저에서 웹 UI를 바로 열 수 있게 해줍니다.

## `app/api/common.py`

- `serialize_row(row)`: DB row를 `dict`로 바꾸고, `datetime`처럼 `isoformat()`이 있는 값은 문자열로 직렬화합니다.
- `success_response(status_code, message, **payload)`: 성공 응답을 공통 JSON 형식으로 감싸서 반환합니다.
- `error_response(status_code, message)`: 실패 응답을 공통 JSON 형식으로 반환합니다.
- `room_not_found_response(room_id)`: room이 없을 때 쓰는 404 응답을 만듭니다.
- `duplicate_message_order_response()`: `message_order` 충돌이 났을 때 쓰는 409 응답을 만듭니다.
- `db_error_response(exc, context_message, status_code=503)`: DB 설정 누락이나 SQL 오류를 공통 형식으로 변환해 반환합니다.

## `app/api/health.py`

- `health_check()`: FastAPI 앱이 살아 있는지 확인하는 단순 헬스체크 응답을 반환합니다.
- `health_db_check()`: DB 연결 상태를 검사하고, 성공이면 200, 실패면 503을 반환합니다.

## `app/api/rooms.py`

- `RoomCreate`: room 생성 요청 본문을 검증하는 Pydantic 모델입니다. 함수는 아니지만, `create_room()`의 입력 스키마 역할을 합니다.
- `create_room(payload)`: `rooms` 테이블에 새 room을 생성하고 생성된 row를 반환합니다.
- `list_rooms()`: 전체 room 목록을 가져옵니다.
- `get_room(room_id)`: 특정 room 1개를 조회합니다.
- `delete_room(room_id)`: room을 삭제합니다. 단, 해당 room에 메시지가 있으면 삭제를 막습니다.

## `app/api/messages.py`

- `MessageCreate`: message 생성 요청 본문 검증용 모델입니다.
- `MessageUpdate`: message 수정 요청 본문 검증용 모델입니다.
- `serialize_message(row)`: message row를 공통 응답 형식에 맞게 직렬화합니다.
- `create_message(payload)`: 메시지를 저장하고, 생성된 메시지를 다시 읽어 응답합니다.
- `list_messages(room_id)`: 전체 메시지 목록 또는 특정 room의 메시지 목록을 조회합니다.
- `get_message(message_id)`: 메시지 1개를 조회합니다.
- `update_message(message_id, payload)`: 메시지 내용을 수정합니다. room이 바뀌면 `message_order`를 다시 계산합니다.
- `delete_message(message_id)`: 메시지 1개를 삭제합니다.

## `app/api/chat.py`

- `ChatRequest`: 채팅 요청 본문을 검증하는 모델입니다.
- `build_assistant_reply(user_content, assistant_mode, history_rows)`: assistant 응답을 만드는 공통 진입점입니다. `echo`면 그대로 돌려주고, 기본값이면 Gemini 응답을 생성합니다.
- `get_default_assistant_mode()`: 환경변수 `CHAT_ASSISTANT_MODE`를 읽어 기본 assistant 동작을 결정합니다.
- `chat(payload)`: 사용자의 메시지를 저장하고, 대화 이력을 바탕으로 assistant 응답도 저장한 뒤 둘 다 반환합니다.

## `app/db/connection.py`

- `get_db_context()`: 에러 메시지에 넣을 `host`와 `database` 값을 환경변수에서 읽어옵니다.
- `get_database_url()`: `MYSQL_*` 환경변수를 조합해 SQLAlchemy용 MySQL URL을 만듭니다.
- `create_db_engine()`: SQLAlchemy `engine`을 생성합니다.
- `db_connection()`: 읽기용 DB 연결 컨텍스트를 제공합니다.
- `db_transaction()`: 쓰기용 트랜잭션 컨텍스트를 제공합니다.
- `check_db_connection()`: `SELECT 1`로 DB 연결이 되는지 확인하고, 결과를 상태 딕셔너리로 반환합니다.

## `app/db/queries.py`

- `fetch_room_by_id(connection, room_id)`: room 1개를 조회합니다.
- `room_exists(connection, room_id)`: room 존재 여부를 확인합니다.
- `room_has_messages(connection, room_id)`: room에 연결된 메시지가 있는지 확인합니다.
- `fetch_message_by_id(connection, message_id)`: message 1개를 조회합니다.
- `get_next_message_order(connection, room_id)`: 해당 room에서 다음으로 들어갈 `message_order` 값을 계산합니다.
- `insert_message(connection, room_id, role, message_order, content)`: 메시지를 insert하고 생성된 ID를 반환합니다.
- `list_recent_room_history(connection, room_id, history_limit)`: 채팅 이력을 최근 순으로 읽어온 뒤, 대화 흐름 순서로 뒤집어서 반환합니다.

## `app/db/schema.py`

- `create_tables(engine)`: `rooms`, `messages` 테이블을 생성합니다.
- `drop_tables(engine)`: `messages`, `rooms` 테이블을 삭제합니다.

## `app/db/sql/messages.py`

- 함수는 없습니다. 메시지 관련 raw SQL 문자열 상수만 정의되어 있습니다.

## `app/db/sql/rooms.py`

- 함수는 없습니다. room 관련 raw SQL 문자열 상수만 정의되어 있습니다.

## `app/db/sql/schema.py`

- 함수는 없습니다. 테이블 생성/삭제용 raw SQL 문자열 상수만 정의되어 있습니다.

## `app/chat_cli.py`

- `request_json(method, path, payload=None)`: API 서버에 JSON 요청을 보내고 상태 코드와 본문을 반환합니다.
- `require_success(status_code, expected_status, body, context)`: CLI용 응답 검증 헬퍼입니다. 상태 코드가 다르면 에러를 발생시킵니다.
- `create_room(room_name)`: API를 통해 room을 생성하고 room ID를 돌려줍니다.
- `list_rooms()`: API에서 room 목록을 가져옵니다.
- `prompt_room_name(prompt)`: 사용자에게 room 이름을 입력받습니다. 빈 값이면 기본 이름을 씁니다.
- `print_info(message)`: 정보 메시지를 출력합니다.
- `print_error(message)`: 에러 메시지를 출력합니다.
- `print_rooms(rooms)`: room 목록을 터미널에 보기 좋게 출력합니다.
- `print_history(room_id)`: 특정 room의 메시지 히스토리를 출력합니다.
- `create_room_from_prompt(prompt)`: 프롬프트로 room 이름을 받고, 그 이름으로 room을 만든 뒤 ID와 이름을 반환합니다.
- `choose_room()`: 기존 room을 고르거나 새 room을 만들도록 사용자를 안내합니다.
- `switch_room()`: room 전환용 안내를 보여주고 `choose_room()`으로 넘깁니다.
- `chat_loop(room_id, room_name)`: CLI 채팅의 메인 루프입니다. 사용자의 입력을 받아 `/chat` API를 호출하고 응답을 출력합니다.
- `main()`: CLI 시작점입니다. room을 고른 뒤 `chat_loop()`를 시작합니다.

## `app/llm.py`

- `generate_assistant_reply(history_rows)`: Gemini API를 호출해 assistant 답변을 생성합니다. 최근 대화 이력을 프롬프트로 사용합니다.

## `app/test_messages_api.py`

### 클래스/헬퍼

- `MessagesApiIntegrationTestCase`: FastAPI 서버와 실제 DB를 함께 검증하는 통합 테스트 클래스입니다.
- `debug(message)`: 테스트 진행 상황을 콘솔에 출력합니다.
- `setUpClass()`: 테스트 시작 전에 DB 엔진을 만들고 테이블을 준비한 뒤 API가 살아 있는지 기다립니다.
- `tearDownClass()`: 테스트 종료 후 DB 엔진을 정리합니다.
- `wait_for_api(timeout_seconds=10)`: FastAPI 서버가 응답할 때까지 `/api/v1/health`를 반복 확인합니다.
- `request_json(method, path, payload=None)`: API에 JSON 요청을 보내고 응답을 파싱합니다.
- `setUp()`: 각 테스트 전에 `rooms`, `messages` 데이터를 비워 초기 상태를 만듭니다.
- `create_room_via_api(name="test room")`: API로 room을 생성하는 보조 함수입니다.
- `chat_once_via_api(room_id, content)`: `/chat` API를 한 번 호출하는 보조 함수입니다.
- `list_room_messages_via_api(room_id)`: 특정 room의 메시지 목록을 API로 조회합니다.
- `list_room_messages_via_db(room_id)`: DB 직접 조회로 특정 room의 메시지 목록을 읽습니다.

### 테스트 함수

- `test_health_db_endpoint()`: DB 헬스체크가 정상 동작하는지 검증합니다.
- `test_rooms_api_create_and_list()`: room 생성과 목록 조회를 검증합니다.
- `test_room_detail_api()`: room 단건 조회를 검증합니다.
- `test_room_delete_api()`: room 삭제와 삭제 후 조회 실패를 검증합니다.
- `test_room_delete_is_blocked_when_messages_exist()`: 메시지가 있는 room은 삭제가 막히는지 검증합니다.
- `test_chat_api_creates_user_and_assistant_messages()`: `/chat`가 user/assistant 메시지를 둘 다 만드는지 검증합니다.
- `test_messages_api_crud_flow()`: 메시지 CRUD 전체 흐름을 검증합니다.
- `test_message_order_is_auto_incremented_in_same_room()`: 같은 room에서 `message_order`가 자동 증가하는지 검증합니다.
- `test_message_order_starts_from_one_in_each_room()`: room이 달라지면 `message_order`가 다시 1부터 시작하는지 검증합니다.
- `test_message_order_is_reassigned_when_room_changes()`: 메시지를 다른 room으로 옮길 때 `message_order`가 재계산되는지 검증합니다.
- `test_chat_history_is_preserved_across_room_switches()`: room을 전환해도 각 room의 대화 이력이 독립적으로 보존되는지 검증합니다.

## `app/test_messages_db.py`

### 클래스/헬퍼

- `MessagesCrudDbTestCase`: DB에 직접 raw SQL을 날리는 CRUD 테스트 클래스입니다.
- `debug(message)`: 테스트 진행 상황을 콘솔에 출력합니다.
- `setUpClass()`: 테스트 시작 전에 DB 엔진을 만들고 테이블을 초기화합니다.
- `tearDownClass()`: 테스트 종료 후 DB 엔진을 정리합니다.
- `setUp()`: 각 테스트 전에 `rooms`, `messages` 데이터를 비웁니다.
- `create_room(name="test room")`: raw SQL로 room을 직접 생성합니다.
- `fetch_message(message_id)`: raw SQL로 message 1개를 읽어옵니다.

### 테스트 함수

- `test_messages_crud_flow()`: raw SQL로 insert, update, delete가 모두 동작하는지 검증합니다.
- `test_duplicate_message_order_is_blocked_in_same_room()`: 같은 room에서 같은 `message_order`를 넣으면 제약조건이 걸리는지 검증합니다.
- `test_same_message_order_is_allowed_in_different_rooms()`: 서로 다른 room에서는 같은 `message_order`가 허용되는지 검증합니다.

## `app/frontend.html`

이 파일은 HTML 안에 JavaScript 함수가 들어 있습니다. 역할별로 보면 다음과 같습니다.

- `setStatus(message)`: 화면 하단 상태 메시지를 갱신합니다.
- `setRoomLabel(roomId, roomName)`: 현재 room 표시를 갱신합니다.
- `setSendingState(nextState)`: 전송 중 UI 비활성화/활성화를 제어합니다.
- `requestJson(path, options={})`: API에 fetch 요청을 보내고 JSON을 읽습니다.
- `appendMessage(role, content)`: 채팅 화면에 메시지 한 줄을 추가합니다.
- `renderHistory(items)`: 현재 room의 메시지 목록을 화면에 렌더링합니다.
- `setCurrentRoom(room)`: 현재 room 상태와 localStorage를 갱신합니다.
- `renderRoomList(items)`: 왼쪽 room 목록을 렌더링합니다.
- `fetchRooms()`: room 목록을 API에서 가져옵니다.
- `refreshRoomList()`: room 목록을 다시 불러오고 화면도 갱신합니다.
- `loadRoomHistory(roomId)`: 특정 room의 메시지 히스토리를 불러옵니다.
- `fetchRoomById(roomId)`: room 단건 정보를 API에서 가져옵니다.
- `selectRoomById(roomId)`: room을 선택하고 그 room의 history를 불러옵니다.
- `createRoom()`: 새 room을 생성하고 그 room으로 전환합니다.
- `boot()`: 페이지 최초 로딩 시 room 목록과 초기 room을 준비합니다.
- `sendMessage(content)`: 현재 room에 메시지를 보내고 user/assistant 응답을 화면에 반영합니다.
- `handleChatSubmit(event)`: 채팅 폼 제출 이벤트를 처리합니다.
- `handleChatInputKeydown(event)`: Enter 키 동작을 처리합니다.
- `handleNewRoomClick()`: 새 room 버튼 클릭을 처리합니다.
- `bindEvents()`: 각 UI 이벤트 핸들러를 연결합니다.

## 함수가 없는 파일

- `app/api/__init__.py`
- `app/db/__init__.py`
- `app/db/sql/__init__.py`
- `app/__init__.py`
- `app/db/sql/messages.py`
- `app/db/sql/rooms.py`
- `app/db/sql/schema.py`

이 파일들은 주로 패키지 초기화나 SQL 상수 정의 용도라서, 별도의 함수는 없습니다.
