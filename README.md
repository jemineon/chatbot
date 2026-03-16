# FastAPI + Docker + MySQL 학습용 최소 뼈대

FastAPI 앱을 Docker로 띄우고, MySQL도 같이 실행해 보려는 초보자를 위한 최소 예제입니다.  
아직 SQLAlchemy, Alembic, ORM 모델은 넣지 않았고, MySQL 연결이 되는지만 `SELECT 1`로 확인하도록 구성했습니다.

## 이번 단계에서 추가된 것

- FastAPI 앱용 `Dockerfile`
- FastAPI + MySQL 개발환경용 `docker-compose.yml`
- 환경변수 예시 파일 `.env.example`
- DB 연결 확인용 코드 `app/db/connection.py`
- Swagger에서 테스트할 수 있는 `GET /api/v1/health/db`

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
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   └── connection.py
│   └── main.py
├── docker-compose.yml
└── requirements.txt
```

## 파일이 왜 필요한가

### `app/main.py`

FastAPI 앱의 시작점입니다. Swagger 문서와 라우터 연결이 여기서 시작됩니다.

### `app/api/health.py`

헬스체크 API를 모아 두는 파일입니다.  
`/health`는 앱 자체가 켜졌는지 확인하고, `/health/db`는 MySQL에 실제로 접속이 되는지 확인합니다.

### `app/core/config.py`

환경변수를 한곳에서 읽는 파일입니다.  
초보자에게 중요한 이유는, 비밀번호나 호스트 주소 같은 값이 코드에 박히지 않고 `.env`로 분리된다는 점입니다.

### `app/db/connection.py`

ORM 없이 MySQL 연결만 테스트하는 아주 얇은 파일입니다.  
지금 단계에서는 테이블 생성이나 조회 대신 `SELECT 1`만 실행해서 연결 성공 여부만 확인합니다.

### `requirements.txt`

Python 패키지 목록입니다.  
`fastapi`는 API 프레임워크, `uvicorn`은 서버, `pydantic-settings`는 환경변수 관리, `PyMySQL`은 MySQL 연결 확인에 사용됩니다.

### `Dockerfile`

FastAPI 앱 이미지를 만드는 설명서입니다.  
내 PC에 Python 환경이 조금 달라도, Docker 안에서는 같은 방식으로 실행되게 도와줍니다.

### `docker-compose.yml`

여러 컨테이너를 함께 띄우는 설정 파일입니다.  
이번 프로젝트에서는 FastAPI 컨테이너와 MySQL 컨테이너를 한 번에 실행하기 위해 필요합니다.

### `.env.example`

`.env`를 만들 때 참고하는 템플릿입니다.  
실제 비밀번호 파일은 보통 Git에 올리지 않기 때문에, 예시 파일을 따로 둡니다.

### `.dockerignore`

Docker 이미지 빌드 때 불필요한 파일을 제외하는 설정입니다.  
예를 들어 `.venv`나 `.git`까지 이미지에 넣지 않아서 빌드가 더 가볍고 빨라집니다.

## 실행 방법

### 1. 환경변수 파일 만들기

`.env.example`을 복사해서 `.env` 파일을 만듭니다.

```bash
cp .env.example .env
```

초보자 관점에서 중요한 포인트:

- `.env.example`은 예시입니다.
- 실제 실행에는 `.env`가 사용됩니다.
- Docker Compose가 이 값을 FastAPI와 MySQL 컨테이너에 전달합니다.

### 2. Docker Compose로 앱과 DB 실행하기

```bash
docker compose up --build
```

이 명령이 하는 일:

- `Dockerfile`로 FastAPI 이미지를 빌드합니다.
- MySQL 컨테이너를 같이 실행합니다.
- FastAPI는 `8000`, MySQL은 `3306` 포트를 사용합니다.

### 3. Swagger 열기

브라우저에서 아래 주소로 들어갑니다.

- Swagger UI: `http://127.0.0.1:8000/docs`

Swagger가 필요한 이유:

- 브라우저에서 직접 API를 눌러 볼 수 있습니다.
- 초보자가 Postman 없이도 빠르게 테스트할 수 있습니다.

### 4. 앱 헬스체크 실행하기

Swagger에서 `GET /api/v1/health`를 실행합니다.

예상 응답:

```json
{
  "status": "ok"
}
```

이 응답은 FastAPI 앱이 정상적으로 뜬 것을 의미합니다.

### 5. DB 연결 헬스체크 실행하기

Swagger에서 `GET /api/v1/health/db`를 실행합니다.

정상 응답 예시:

```json
{
  "status": "ok",
  "message": "MySQL connection succeeded.",
  "database": "fastapi_app",
  "host": "mysql",
  "ping": 1
}
```

이 단계에서 중요한 점:

- 아직 테이블은 만들지 않습니다.
- ORM도 쓰지 않습니다.
- 단순히 MySQL 컨테이너가 떠 있고, FastAPI가 그 컨테이너에 접속 가능한지만 확인합니다.

## `docker-compose.yml`에서 눈여겨볼 설정

### `env_file`

`.env` 값을 컨테이너에 넣어 주는 설정입니다.  
코드 수정 없이 환경별 값을 바꾸기 쉬워집니다.

### `depends_on`

FastAPI가 MySQL보다 먼저 켜져서 연결 실패하는 상황을 줄이기 위한 설정입니다.  
여기서는 MySQL 헬스체크가 통과한 뒤 API가 따라 올라오게 했습니다.

### `healthcheck`

MySQL이 "컨테이너만 켜진 상태"가 아니라 "실제로 응답 가능한 상태"인지 확인합니다.  
초보자 입장에서는 이 설정이 있어야 왜 API가 바로 DB에 못 붙는지 이해하기 쉽습니다.

### `volumes`

MySQL 데이터는 컨테이너를 다시 만들어도 유지되게 했습니다.  
앱 코드는 로컬 수정이 바로 컨테이너에 반영되도록 `./app:/code/app`으로 연결했습니다.

## 학습 단계 메모

- 지금은 DB 연결 확인까지만 했습니다.
- 다음 단계에서 SQLAlchemy, Alembic, ORM 모델을 추가하면 됩니다.
- 만약 Docker 없이 로컬에서 FastAPI만 실행하고 싶다면 `MYSQL_HOST`를 `127.0.0.1`로 바꿔야 할 수 있습니다.
