SELECT_NEXT_MESSAGE_ORDER_SQL = """
SELECT COALESCE(MAX(message_order), 0) + 1 AS next_message_order
FROM messages
WHERE room_id = :room_id
"""

SELECT_MESSAGE_BY_ID_SQL = """
SELECT id, room_id, role, message_order, content, created_at
FROM messages
WHERE id = :message_id
"""

INSERT_MESSAGE_SQL = """
INSERT INTO messages (room_id, role, message_order, content)
VALUES (:room_id, :role, :message_order, :content)
"""

LIST_ALL_MESSAGES_SQL = """
SELECT id, room_id, role, message_order, content, created_at
FROM messages
ORDER BY room_id, message_order, id
"""

LIST_MESSAGES_BY_ROOM_SQL = """
SELECT id, room_id, role, message_order, content, created_at
FROM messages
WHERE room_id = :room_id
ORDER BY room_id, message_order, id
"""

LIST_RECENT_MESSAGES_BY_ROOM_SQL = """
SELECT id, room_id, role, message_order, content, created_at
FROM messages
WHERE room_id = :room_id
ORDER BY message_order DESC, id DESC
LIMIT :history_limit
"""

UPDATE_MESSAGE_SQL = """
UPDATE messages
SET room_id = :room_id,
    role = :role,
    message_order = :message_order,
    content = :content
WHERE id = :message_id
"""

DELETE_MESSAGE_SQL = """
DELETE FROM messages
WHERE id = :message_id
"""
