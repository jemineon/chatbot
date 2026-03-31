CHECK_ROOM_EXISTS_SQL = """
SELECT id
FROM rooms
WHERE id = :room_id
"""

SELECT_ROOM_BY_ID_SQL = """
SELECT id, name, created_at
FROM rooms
WHERE id = :room_id
"""

INSERT_ROOM_SQL = """
INSERT INTO rooms (name)
VALUES (:name)
"""

LIST_ROOMS_SQL = """
SELECT id, name, created_at
FROM rooms
ORDER BY id
"""

DELETE_ROOM_SQL = """
DELETE FROM rooms
WHERE id = :room_id
"""

CHECK_ROOM_HAS_MESSAGES_SQL = """
SELECT id
FROM messages
WHERE room_id = :room_id
LIMIT 1
"""
