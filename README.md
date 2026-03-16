# FastAPI 학습용 최소 뼈대

FastAPI를 처음 연습할 때 바로 실행해 볼 수 있도록 만든 아주 작은 예제입니다.

## 포함된 기능

- `GET /api/v1/health` 엔드포인트
- Swagger UI에서 테스트 가능
- DB 연결 없음
- Docker 설정 없음

## 프로젝트 구조

```text
.
├── app/
│   ├── api/
│   │   └── health.py
│   └── main.py
├── requirements.txt
└── README.md
```

## 파일 설명

### `app/main.py`

FastAPI 앱이 시작되는 진입점입니다. 애플리케이션 객체를 만들고, `health` 라우터를 `/api/v1` 경로에 연결합니다. Swagger 문서도 이 앱 객체를 기준으로 생성됩니다.

### `app/api/health.py`

가장 간단한 API 예제를 담는 파일입니다. `GET /api/v1/health` 요청이 들어오면 서버가 살아 있는지 확인할 수 있도록 `{"status": "ok"}`를 반환합니다.

### `requirements.txt`

프로젝트 실행에 필요한 최소 패키지 목록입니다. `fastapi`는 웹 API 프레임워크이고, `uvicorn`은 개발용 서버 실행 도구입니다.

### `README.md`

프로젝트를 처음 보는 사람도 바로 실행해 볼 수 있도록 실행 방법과 파일 역할을 짧게 정리한 안내 문서입니다.

## 설치

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 실행

```bash
uvicorn app.main:app --reload
```

서버가 실행되면 아래 주소를 사용할 수 있습니다.

- API 엔드포인트: `http://127.0.0.1:8000/api/v1/health`
- Swagger UI: `http://127.0.0.1:8000/docs`

## 응답 예시

```json
{
  "status": "ok"
}
```
