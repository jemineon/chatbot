# 메시지 관리 구조

이 문서는 현재 프로젝트에서 `messages` 데이터가 어떻게 저장되고, 어떤 규칙으로 관리되는지 짧게 정리한 문서입니다.

## 핵심 개념

이 프로젝트는 `messages` 테이블을 채팅 로그 저장소처럼 사용합니다.

- 하나의 room 안에 여러 message가 들어감
- 각 message는 `role` 값을 가짐
- 같은 room 안에서는 `message_order`로 순서를 관리함

즉, "대화방 하나" 안에 "순서가 있는 메시지 목록"이 쌓이는 구조입니다.

## messages 테이블 컬럼

- `id`: 메시지 고유 번호
- `room_id`: 어떤 room에 속한 메시지인지 나타냄
- `role`: `user`, `assistant`, `system`
- `message_order`: 같은 room 안에서의 순서
- `content`: 실제 메시지 내용
- `created_at`: 생성 시각

## 메시지 생성 규칙

메시지를 만들 때 클라이언트가 `message_order`를 직접 넣지 않습니다.  
서버가 같은 room 안의 마지막 순서를 찾아서 자동으로 다음 번호를 붙입니다.

예를 들면:

- 첫 메시지 -> `message_order = 1`
- 두 번째 메시지 -> `message_order = 2`
- 세 번째 메시지 -> `message_order = 3`

이 규칙은 [app/api/messages.py](/Users/hanwha/Desktop/jemin/work/chatbot_project/app/api/messages.py#L1) 와 [app/db/sql/messages.py](/Users/hanwha/Desktop/jemin/work/chatbot_project/app/db/sql/messages.py#L1) 에 구현되어 있습니다.

## DB 제약조건

DB에서도 한 번 더 안전장치를 둡니다.

- 같은 `room_id` 안에서는 같은 `message_order`를 사용할 수 없음

즉 API에서 먼저 순서를 계산하고, DB가 마지막으로 중복을 막아 주는 구조입니다.

이 제약조건은 [app/db/sql/schema.py](/Users/hanwha/Desktop/jemin/work/chatbot_project/app/db/sql/schema.py#L1) 의 `uq_messages_room_id_message_order` 에 있습니다.

## 채팅 API에서의 저장 방식

`POST /api/v1/chat` 은 메시지 1개만 저장하지 않습니다.  
한 번 호출되면 보통 아래 2개를 같이 저장합니다.

1. user 메시지 저장
2. assistant 응답 생성 후 assistant 메시지 저장

즉 대화 한 턴이 끝나면, DB에는 보통 message가 2개 추가됩니다.

이 흐름은 [app/api/chat.py](/Users/hanwha/Desktop/jemin/work/chatbot_project/app/api/chat.py#L1) 에 있습니다.

## 히스토리 조회 방식

현재 메시지 히스토리는 room 기준으로 조회합니다.

- `GET /api/v1/messages`
- `GET /api/v1/messages?room_id=1`

브라우저 프론트와 CLI 모두 이 방식으로 기존 대화를 다시 불러옵니다.

## 현재 상태에서 가능한 것

- room별 메시지 저장
- room별 메시지 조회
- message 단건 조회
- message 수정
- message 삭제
- chat API를 통한 user/assistant 메시지 동시 저장
- 브라우저에서 room 선택 후 이전 대화 이어가기
- CLI에서 room 선택 후 이전 대화 이어가기

## 아직 없는 것

현재는 학습용 최소 구조라서 아래는 아직 없습니다.

- soft delete
- edit history
- 검색
- 페이지네이션
- 첨부파일
- 사용자별 권한 관리
- 메시지 요약/압축 저장

## 관련 파일

- [app/api/messages.py](/Users/hanwha/Desktop/jemin/work/chatbot_project/app/api/messages.py#L1)
- [app/api/chat.py](/Users/hanwha/Desktop/jemin/work/chatbot_project/app/api/chat.py#L1)
- [app/db/sql/messages.py](/Users/hanwha/Desktop/jemin/work/chatbot_project/app/db/sql/messages.py#L1)
- [app/db/sql/schema.py](/Users/hanwha/Desktop/jemin/work/chatbot_project/app/db/sql/schema.py#L1)
