# 다른 컴퓨터에서 실행하기

이 문서는 이 프로젝트를 Git에서 내려받아, **다른 컴퓨터에서 처음 실행하는 사람** 기준으로 정리한 실행 가이드입니다.  
개발 경험이 많지 않아도 순서대로 따라가면 브라우저에서 채팅 화면까지 열 수 있게 작성했습니다.

## 이 문서가 필요한 이유

이 프로젝트는 아래 3가지를 함께 씁니다.

- FastAPI: 웹 서버와 API 실행
- MySQL: 대화방과 메시지 저장
- Docker Compose: FastAPI와 MySQL을 한 번에 실행

즉, 단순히 Python 파일 하나만 실행하는 프로젝트가 아니라, **컨테이너 2개를 같이 띄워야 하는 구조**입니다.

## 준비물

다른 컴퓨터에 아래가 설치되어 있어야 합니다.

- Git
- Docker Desktop

확인 명령:

```bash
git --version
docker --version
docker compose version
```

위 명령 중 하나라도 동작하지 않으면 먼저 설치가 필요합니다.

## 1. 프로젝트 내려받기

원하는 폴더로 이동한 뒤 저장소를 clone 합니다.

```bash
git clone <your-repo-url>
cd chatbot_project
```

`<your-repo-url>` 부분에는 실제 Git 저장소 주소를 넣으면 됩니다.

## 2. 환경변수 파일 만들기

이 프로젝트는 실행에 필요한 설정을 `.env` 파일에서 읽습니다.  
예시 파일이 이미 있으니, 그 파일을 복사해서 실제 실행용 파일을 만듭니다.

```bash
cp .env.example .env
```

왜 이 단계가 필요한가:

- `.env.example` 는 샘플
- `.env` 는 실제 실행 때 Docker와 FastAPI가 읽는 파일

## 3. `.env` 값 채우기

최소한 아래 값은 확인해야 합니다.

```env
MYSQL_HOST=db
MYSQL_PORT=3306
MYSQL_DATABASE=fastapi_app
MYSQL_USER=fastapi_user
MYSQL_PASSWORD=fastapi_password
MYSQL_ROOT_PASSWORD=rootpassword
GEMINI_API_KEY=your_google_ai_studio_api_key
GEMINI_MODEL=gemini-2.5-flash-lite
CHAT_ASSISTANT_MODE=gemini
```

중요한 포인트:

- `MYSQL_HOST=db` 는 Docker Compose 안에서 MySQL 서비스 이름입니다
- `GEMINI_API_KEY` 는 직접 본인 키로 바꿔야 실제 LLM 응답이 됩니다
- `GEMINI_MODEL=gemini-2.5-flash-lite` 는 현재 비용을 낮추기 위한 기본 모델입니다

만약 Gemini 호출 없이 구조만 확인하고 싶다면:

```env
CHAT_ASSISTANT_MODE=echo
```

로 바꾸면 됩니다. 이 경우 assistant가 실제 LLM 대신 `Echo: ...` 형태로 응답합니다.

## 4. Docker Desktop 켜기

macOS나 Windows에서는 Docker Desktop 앱이 실제로 실행 중이어야 합니다.  
앱이 꺼져 있으면 `docker compose up` 이 실패합니다.

확인 명령:

```bash
docker ps
```

정상이라면 에러 없이 빈 목록 또는 컨테이너 목록이 나옵니다.

## 5. 컨테이너 실행

프로젝트 루트에서 아래 명령을 실행합니다.

```bash
docker compose up --build
```

무슨 일이 일어나나:

- `api` 컨테이너가 FastAPI 서버를 실행
- `db` 컨테이너가 MySQL 서버를 실행
- 이미지가 없으면 자동으로 다운로드

처음에는 이미지 다운로드 때문에 시간이 조금 걸릴 수 있습니다.

백그라운드 실행을 원하면:

```bash
docker compose up -d --build
```

## 6. 테이블 생성

이 프로젝트는 **FastAPI 시작 시 테이블을 자동 생성하지 않습니다.**  
학습용으로 DB 연결과 테이블 생성 단계를 분리해 둔 상태입니다.

그래서 컨테이너를 띄운 뒤 아래 명령을 한 번 실행해야 합니다.

```bash
docker compose exec -T api python -c "from app.db.connection import create_db_engine; from app.db.schema import create_tables; engine = create_db_engine(); create_tables(engine); engine.dispose(); print('rooms/messages tables created')"
```

이 명령이 하는 일:

- FastAPI 코드 안의 DB 연결 함수를 사용
- `rooms`, `messages` 테이블 생성

## 7. 실행 확인

브라우저에서 아래 주소를 열어 확인합니다.

- 프론트엔드: `http://127.0.0.1:8000/`
- Swagger 문서: `http://127.0.0.1:8000/docs`

먼저 확인하면 좋은 순서:

1. `http://127.0.0.1:8000/docs`
2. `GET /api/v1/health`
3. `GET /api/v1/health/db`
4. `http://127.0.0.1:8000/`

정상이라면:

- health API 는 앱 상태를 보여줌
- health/db API 는 MySQL 연결 성공 여부를 보여줌
- `/` 에서는 채팅 화면이 열림

## 8. 실제 채팅 테스트

브라우저 채팅 화면에서:

1. 페이지를 열면 room 목록을 불러옵니다
2. room이 없으면 새 room이 자동 생성됩니다
3. 메시지를 입력하면 `POST /api/v1/chat` 이 호출됩니다
4. user 메시지와 assistant 메시지가 모두 DB에 저장됩니다

LLM이 실제로 켜져 있으면 Gemini 응답이 오고,  
`CHAT_ASSISTANT_MODE=echo` 면 테스트용 echo 응답이 옵니다.

## 9. DB 저장 확인

다른 컴퓨터에서도 DB에 실제로 저장되는지 바로 확인할 수 있습니다.

최근 room과 메시지 보기:

```bash
docker compose exec db sh -lc 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" -D "$MYSQL_DATABASE" -e "SELECT id, name, created_at FROM rooms ORDER BY id DESC LIMIT 5; SELECT id, room_id, role, message_order, content, created_at FROM messages ORDER BY id DESC LIMIT 20;"'
```

특정 room만 보기:

```bash
docker compose exec db sh -lc 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" -D "$MYSQL_DATABASE" -e "SELECT id, role, message_order, content, created_at FROM messages WHERE room_id = 1 ORDER BY message_order;"'
```

위 예시의 `1`은 실제 room id로 바꾸면 됩니다.

## 10. 테스트 실행

DB 직접 테스트:

```bash
docker compose exec api python -m unittest -v app.test_messages_db
```

HTTP API 테스트:

```bash
docker compose exec api python -m unittest -v app.test_messages_api
```

이 테스트들은 다른 컴퓨터에서도 구조가 제대로 올라왔는지 확인하는 좋은 기준입니다.

## 11. 종료 방법

실행 중인 컨테이너를 종료하려면:

```bash
docker compose down
```

DB 데이터까지 완전히 초기화하려면:

```bash
docker compose down -v
```

주의:

- `down` 은 컨테이너만 내림
- `down -v` 는 MySQL 데이터 볼륨까지 삭제

즉 `down -v` 후 다시 실행하면 예전 room/messages 데이터는 사라집니다.

## 자주 막히는 문제

### 1. `.env`를 바꿨는데 비밀번호가 안 바뀜

이미 MySQL 볼륨이 만들어진 뒤라면, `MYSQL_PASSWORD` 같은 초기화 값은 자동 반영되지 않을 수 있습니다.  
학습용으로 가장 쉬운 해결은:

```bash
docker compose down -v
docker compose up -d --build
```

그리고 다시 테이블 생성 명령을 실행하는 것입니다.

### 2. `docker.sock` 에러가 남

대부분 Docker Desktop이 꺼져 있을 때 생깁니다.  
먼저 Docker Desktop을 켠 뒤 다시 실행합니다.

### 3. `/api/v1/health/db` 가 실패함

아래를 순서대로 확인합니다.

- `.env` 값이 맞는지
- `docker compose ps` 에서 `db` 컨테이너가 떠 있는지
- 테이블 생성 전이라면 먼저 create_tables 명령을 실행했는지

### 4. 브라우저 화면은 뜨는데 응답이 안 옴

대부분 `GEMINI_API_KEY` 문제이거나, `CHAT_ASSISTANT_MODE=gemini` 상태에서 외부 호출이 실패한 경우입니다.  
이럴 때는 먼저:

```env
CHAT_ASSISTANT_MODE=echo
```

로 바꿔서 구조 자체가 정상인지 확인하는 게 좋습니다.

## 추천 실행 순서 요약

다른 컴퓨터에서 가장 추천하는 순서는 아래입니다.

```bash
git clone <your-repo-url>
cd chatbot_project
cp .env.example .env
# .env 에 GEMINI_API_KEY 입력
docker compose up -d --build
docker compose exec -T api python -c "from app.db.connection import create_db_engine; from app.db.schema import create_tables; engine = create_db_engine(); create_tables(engine); engine.dispose(); print('rooms/messages tables created')"
```

그 다음 브라우저에서:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/`

를 열면 됩니다.
