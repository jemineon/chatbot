# FastAPI + Docker + MySQL room/messages 학습 예제

이 단계는 Docker Compose 환경에서 FastAPI가 MySQL에 연결하고, `rooms`와 `messages` 테이블을 SQLAlchemy Core 방식으로 직접 다루는 학습 예제입니다.  
아직 ORM 모델, Session, Alembic, repository/service 레이어는 넣지 않았고, `engine`, `Table`, `MetaData` 중심으로 흐름을 익히는 데 집중합니다.

## 프로젝트 구조

```text
.
├── .dockerignore
├── .env.example
├── Dockerfile
├── README.md
├── app/
│   ├── api/
│   │   ├── health.py
│   │   ├── messages.py
│   │   └── rooms.py
│   ├── db/
│   │   ├── connection.py
│   │   └── schema.py
│   ├── main.py
│   ├── test_messages_api.py
│   └── test_messages_db.py
├── docker-compose.yml
└── requirements.txt
```

## 파일이 왜 나뉘어 있나

### `app/main.py`

FastAPI 앱 시작점입니다.  
health, rooms, messages 라우터를 한곳에서 연결합니다.

### `app/api/health.py`

헬스체크 API를 모아 둔 파일입니다.  
앱이 살아 있는지, DB 연결이 되는지 가장 먼저 확인할 수 있습니다.

### `app/api/rooms.py`

room 생성과 조회를 담당하는 최소 API 파일입니다.  
이제 메시지는 room에 속해야 하므로, 먼저 room을 만들 수 있어야 학습 흐름이 자연스럽습니다.

### `app/api/messages.py`

메시지 CRUD API를 담는 파일입니다.  
메시지를 생성할 때 `message_order`를 자동으로 붙여 주고, room이 바뀌면 새 room 기준으로 다시 순서를 계산합니다.

### `app/db/connection.py`

DB 연결만 담당하는 파일입니다.  
환경변수를 직접 읽어서 `DATABASE_URL`을 만들고, SQLAlchemy `engine`을 생성합니다.

### `app/db/schema.py`

테이블 구조만 담당하는 파일입니다.  
`rooms`, `messages` 테이블과 foreign key, unique constraint를 한눈에 볼 수 있습니다.

### `app/test_messages_db.py`

DB에 직접 붙어서 CRUD와 제약조건을 확인하는 테스트입니다.  
API를 거치지 않고, 테이블 규칙이 DB에서 실제로 동작하는지 보는 용도입니다.

### `app/test_messages_api.py`

실제 HTTP 요청으로 FastAPI API를 검증하는 통합 테스트입니다.  
Swagger에서 따라하는 흐름과 가장 비슷합니다.

## 초보자용 핵심 개념

### Engine

DB와 실제로 연결해 주는 객체입니다.  
지금 단계에서는 "MySQL에 붙는 통로"라고 이해하면 충분합니다.

### Table

파이썬 코드로 테이블 구조를 표현한 것입니다.  
컬럼 이름, 타입, PK, foreign key, unique constraint를 코드로 적습니다.

### MetaData

테이블 정의들을 모아 두는 상자 같은 객체입니다.  
`metadata.create_all(engine)`를 호출하면 여기에 등록된 테이블들을 실제 DB에 만들 수 있습니다.

## 이번 단계에서 배우는 포인트

- `rooms`와 `messages`를 foreign key로 연결하는 방법
- 같은 room 안에서만 `message_order` 중복을 막는 방법
- `message_order`를 사용자가 직접 주지 않고 서버가 자동 계산하는 방법
- API에서 먼저 검사하고, DB 제약조건으로 한 번 더 막는 이중 방어 방식
- DB 직접 테스트와 HTTP API 테스트를 나눠서 보는 방법

## 환경변수 의미

- `MYSQL_HOST`: Docker Compose 안에서 MySQL 서비스 이름인 `db`
- `MYSQL_PORT`: MySQL 포트
- `MYSQL_DATABASE`: 접속할 데이터베이스 이름
- `MYSQL_USER`: 앱이 사용할 사용자 이름
- `MYSQL_PASSWORD`: 앱이 사용할 비밀번호
- `MYSQL_ROOT_PASSWORD`: MySQL 컨테이너 초기화용 루트 비밀번호

## Docker 기준 실행 방법

### 1. `.env` 파일 만들기

```bash
cp .env.example .env
```

### 2. 컨테이너 실행하기

```bash
docker compose up --build
```

### 3. 이전 단계에서 이미 DB를 만들었다면 초기화하기

이번 단계에서는 `rooms` 테이블과 `messages(room_id, message_order)` 고유 제약조건이 새로 추가됐습니다.  
이미 예전 스키마로 `messages` 테이블이 만들어져 있었다면 `create_all()`만으로는 기존 테이블 구조가 바뀌지 않습니다.

학습용으로 가장 단순한 방법은 볼륨을 지우고 다시 시작하는 것입니다.

```bash
docker compose down -v
docker compose up --build
```

### 4. 테이블 생성하기

FastAPI 시작 시 자동 생성은 아직 하지 않으므로, 아래 명령으로 직접 생성합니다.

```bash
docker compose exec -T api python -c "from app.db.connection import create_db_engine; from app.db.schema import create_tables; engine = create_db_engine(); create_tables(engine); engine.dispose(); print('rooms/messages tables created')"
```

### 5. Swagger 열기

브라우저에서 아래 주소로 접속합니다.

- `http://127.0.0.1:8000/docs`

## 확인할 엔드포인트

### `GET /api/v1/health`

FastAPI 앱이 실행 중인지 확인합니다.

### `GET /api/v1/health/db`

MySQL 연결이 되는지 `SELECT 1 AS ping`으로 확인합니다.

### `POST /api/v1/rooms`

메시지를 담을 room 1개를 생성합니다.

예시 요청 본문:

```json
{
  "name": "첫 번째 대화방"
}
```

### `GET /api/v1/rooms`

현재 생성된 room 목록을 조회합니다.

### `POST /api/v1/messages`

메시지 1개를 저장합니다.  
먼저 room을 만들고, 그 응답으로 받은 `id`를 `room_id`에 넣어야 합니다.  
`message_order`는 서버가 자동으로 계산하므로 요청에 넣지 않습니다.

예시 요청 본문:

```json
{
  "room_id": 1,
  "role": "user",
  "content": "안녕하세요"
}
```

### `GET /api/v1/messages`

전체 메시지 목록을 조회합니다.  
`room_id` 쿼리 파라미터를 주면 특정 room 메시지만 볼 수 있습니다.

예시:

```text
GET /api/v1/messages
GET /api/v1/messages?room_id=1
```

### `GET /api/v1/messages/{message_id}`

메시지 1개를 조회합니다.

### `PUT /api/v1/messages/{message_id}`

메시지 1개를 수정합니다.  
요청 본문은 `POST /api/v1/messages`와 같은 형태를 사용합니다.  
같은 room 안에서 수정하면 기존 `message_order`를 유지하고, 다른 room으로 옮기면 새 room의 마지막 순서 뒤에 자동으로 붙습니다.

### `DELETE /api/v1/messages/{message_id}`

메시지 1개를 삭제합니다.

## 추천 사용 순서

1. `POST /api/v1/rooms` 실행
2. 응답으로 받은 `id` 확인
3. 그 값을 사용해서 `POST /api/v1/messages` 실행
4. `GET /api/v1/messages?room_id=...` 로 조회

## 테이블 구조

### rooms

- `id`: PK, auto increment
- `name`: room 이름
- `created_at`: 생성 시각

### messages

- `id`: PK, auto increment
- `room_id`: `rooms.id`를 참조하는 foreign key
- `role`: `user`, `assistant`, `system` 값을 담는 문자열 컬럼
- `message_order`: 같은 room 안에서의 메시지 순서
- `content`: 메시지 본문
- `created_at`: 생성 시각

추가 규칙:

- 같은 `room_id` 안에서는 `message_order`가 중복될 수 없습니다
- 다른 room이면 같은 `message_order` 값을 사용해도 됩니다
- 새 메시지를 만들면 같은 room의 마지막 순서 다음 번호가 자동으로 들어갑니다
- 메시지를 다른 room으로 옮기면 새 room 기준으로 순서가 다시 계산됩니다

## 테이블 생성은 아직 수동 호출 방식

이번 단계에서는 FastAPI가 시작될 때 자동으로 테이블을 만들지 않습니다.  
학습 목적상 "테이블 정의"와 "실제 생성 호출"을 분리해서 보는 편이 이해에 더 도움이 되기 때문입니다.

이 방식의 학습 포인트:

- DB 연결 코드와 테이블 정의 코드를 분리해서 볼 수 있습니다
- SQLAlchemy ORM 없이도 테이블을 만들 수 있다는 점을 이해할 수 있습니다
- 제약조건이 API 검증과 DB 검증 양쪽에서 어떻게 동작하는지 볼 수 있습니다
- 다음 단계에서 ORM이나 Alembic을 붙이기 전에 Core 방식의 기본 흐름을 먼저 익힐 수 있습니다

## 테스트 실행

### DB 직접 CRUD 테스트

```bash
docker compose exec api python -m unittest -v app.test_messages_db
```

### HTTP API 통합 테스트

```bash
docker compose exec api python -m unittest -v app.test_messages_api
```

## 이번 단계에서 일부러 넣지 않은 것

- ORM declarative model
- Session / SessionLocal
- Alembic / migration
- 채팅 API
- repository / service 패턴
