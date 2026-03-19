# FastAPI + Docker + MySQL messages 테이블 학습 예제

이 단계는 Docker Compose 환경에서 FastAPI가 MySQL에 연결하고, `messages` 테이블을 직접 정의해서 수동으로 생성해보는 최소 학습 예제입니다.  
아직 ORM 모델, Session, Alembic, repository/service 레이어는 넣지 않았고, SQLAlchemy `engine`과 `Table` 정의만 사용합니다.

## 프로젝트 구조

```text
.
├── .dockerignore
├── .env.example
├── Dockerfile
├── README.md
├── app/
│   ├── api/
│   │   └── health.py
│   ├── db/
│   │   ├── connection.py
│   │   └── schema.py
│   └── main.py
├── docker-compose.yml
└── requirements.txt
```

## 파일이 왜 나뉘어 있나

### `app/main.py`

FastAPI 앱의 진입점입니다.  
이번 단계에서는 최소 구조만 유지하기 위해 health 라우터만 연결합니다.

### `app/api/health.py`

헬스체크 API를 모아 둔 파일입니다.  
앱이 살아 있는지, DB 연결이 되는지 가장 먼저 확인할 수 있도록 분리했습니다.

### `app/db/connection.py`

DB 연결만 담당하는 파일입니다.  
환경변수를 직접 읽어서 `DATABASE_URL`을 만들고, SQLAlchemy `engine`과 연결 확인 함수를 제공합니다.

### `app/db/schema.py`

테이블 정의만 담당하는 파일입니다.  
`MetaData`, `Table`, `Column`으로 `messages` 테이블 구조를 직접 적어 보면서 SQLAlchemy Core 방식을 익히기 좋습니다.

## 초보자용 핵심 개념

### Engine

DB와 실제로 연결해 주는 객체입니다.  
지금 단계에서는 "MySQL에 붙는 통로" 정도로 이해하면 충분합니다.

### Table

파이썬 코드로 테이블 구조를 표현한 것입니다.  
컬럼 이름, 타입, PK 같은 정보를 코드로 적습니다.

### MetaData

테이블 정의들을 모아 두는 상자 같은 객체입니다.  
`metadata.create_all(engine)`를 호출하면 여기에 등록된 테이블들을 실제 DB에 생성할 수 있습니다.

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

### 3. Swagger 열기

브라우저에서 아래 주소로 접속합니다.

- `http://127.0.0.1:8000/docs`

## 확인할 엔드포인트

### `GET /api/v1/health`

FastAPI 앱이 실행 중인지 확인합니다.

### `GET /api/v1/health/db`

MySQL 연결이 되는지 `SELECT 1 AS ping`으로 확인합니다.

성공 예시:

```json
{
  "status": "ok",
  "message": "MySQL connection succeeded.",
  "host": "db",
  "database": "fastapi_app",
  "ping": 1
}
```

## messages 테이블 구조

`app/db/schema.py`에는 아래 컬럼이 정의되어 있습니다.

- `id`: PK, auto increment
- `room_id`: 이후 멀티룸 확장을 위한 정수 컬럼
- `role`: `user`, `assistant`, `system` 등을 담는 문자열 컬럼
- `message_order`: 같은 room 안에서의 순서
- `content`: 메시지 본문
- `created_at`: 생성 시각

## 테이블 생성은 아직 수동 호출 방식

이번 단계에서는 FastAPI가 시작될 때 자동으로 테이블을 만들지 않습니다.  
학습 목적상 "테이블 정의"와 "실제 생성 호출"을 분리해서 보는 편이 이해에 더 도움이 되기 때문입니다.

테이블을 직접 생성해보려면, 컨테이너가 실행 중인 상태에서 아래 명령을 실행합니다.

```bash
docker compose exec -T api python -c "from app.db.connection import create_db_engine; from app.db.schema import create_tables; engine = create_db_engine(); create_tables(engine); engine.dispose(); print('messages table created')"
```

이 방식의 학습 포인트:

- DB 연결 코드와 테이블 정의 코드를 분리해서 볼 수 있습니다.
- SQLAlchemy ORM 없이도 테이블을 만들 수 있다는 점을 이해할 수 있습니다.
- 다음 단계에서 ORM이나 Alembic을 붙이기 전에, Core 방식의 기본 흐름을 먼저 익힐 수 있습니다.

## 이번 단계에서 일부러 넣지 않은 것

- ORM declarative model
- Session / SessionLocal
- Alembic / migration
- rooms 테이블
- 메시지 저장 API
- 채팅 API
- repository / service 패턴
