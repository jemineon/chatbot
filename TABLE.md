# 테이블 구조 정리

이 문서는 현재 코드 기준으로 MySQL에 만들어지는 테이블 구조를 정리한 자료입니다.  
스키마의 기준은 [app/db/sql/schema.py](./app/db/sql/schema.py)와 [app/db/schema.py](./app/db/schema.py)입니다.

## 전체 구조

- `rooms`: 대화방 정보를 저장합니다.
- `messages`: 각 대화방에 속한 메시지를 저장합니다.

`messages.room_id`는 `rooms.id`를 참조하는 foreign key입니다.  
또한 같은 room 안에서는 `message_order`가 중복되지 않도록 unique 제약이 걸려 있습니다.

## `rooms`

### 용도

대화방 자체를 저장하는 테이블입니다.  
웹 UI, CLI, chat API 모두 이 room을 기준으로 대화를 구분합니다.

### 컬럼

| 컬럼명 | 타입 | 제약조건 | 설명 |
|---|---|---|---|
| `id` | `INT` | `PRIMARY KEY`, `AUTO_INCREMENT` | room 식별자 |
| `name` | `VARCHAR(100)` | `NOT NULL` | room 이름 |
| `created_at` | `DATETIME` | `NOT NULL`, `DEFAULT CURRENT_TIMESTAMP` | 생성 시각 |

### 생성 SQL

```sql
CREATE TABLE IF NOT EXISTS rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
)
```

## `messages`

### 용도

각 room 안에 저장되는 메시지를 보관하는 테이블입니다.  
사용자 메시지와 assistant 메시지를 모두 여기에 저장합니다.

### 컬럼

| 컬럼명 | 타입 | 제약조건 | 설명 |
|---|---|---|---|
| `id` | `INT` | `PRIMARY KEY`, `AUTO_INCREMENT` | message 식별자 |
| `room_id` | `INT` | `NOT NULL`, `FOREIGN KEY -> rooms(id)` | 속한 room ID |
| `role` | `VARCHAR(20)` | `NOT NULL` | `user`, `assistant`, `system` 같은 역할 |
| `message_order` | `INT` | `NOT NULL` | room 안에서의 메시지 순서 |
| `content` | `TEXT` | `NOT NULL` | 메시지 본문 |
| `created_at` | `DATETIME` | `NOT NULL`, `DEFAULT CURRENT_TIMESTAMP` | 생성 시각 |

### 제약조건

- `CONSTRAINT fk_messages_room_id FOREIGN KEY (room_id) REFERENCES rooms(id)`
- `CONSTRAINT uq_messages_room_id_message_order UNIQUE (room_id, message_order)`

### 생성 SQL

```sql
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    role VARCHAR(20) NOT NULL,
    message_order INT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_messages_room_id FOREIGN KEY (room_id) REFERENCES rooms(id),
    CONSTRAINT uq_messages_room_id_message_order UNIQUE (room_id, message_order)
)
```

## 생성/삭제 순서

### 생성

1. `rooms`
2. `messages`

`messages`가 `rooms.id`를 참조하므로, room 테이블이 먼저 있어야 합니다.

### 삭제

1. `messages`
2. `rooms`

참조 관계가 있으므로, 메시지를 먼저 비우거나 삭제한 뒤 room을 처리하는 것이 안전합니다.

## 현재 코드에서 쓰는 파일

- [app/db/schema.py](./app/db/schema.py): `create_tables(engine)`, `drop_tables(engine)`
- [app/db/sql/schema.py](./app/db/sql/schema.py): 실제 `CREATE TABLE` / `DROP TABLE` SQL 문자열
- [app/db/sql/rooms.py](./app/db/sql/rooms.py): room 관련 조회/삭제 SQL
- [app/db/sql/messages.py](./app/db/sql/messages.py): message 관련 조회/삽입/수정/삭제 SQL
