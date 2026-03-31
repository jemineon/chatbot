import json
import os
from typing import Any, Dict, List, Mapping
from urllib import error, request


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"
DEFAULT_GEMINI_HISTORY_LIMIT = 8


def generate_assistant_reply(history_rows: List[Mapping[str, Any]]) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "")

    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY in your environment.")

    contents = []
    for row in history_rows[-DEFAULT_GEMINI_HISTORY_LIMIT:]:
        gemini_role = "model" if row["role"] == "assistant" else "user"
        contents.append(
            {
                "role": gemini_role,
                "parts": [{"text": row["content"]}],
            }
        )

    payload = {
        "systemInstruction": {
            "parts": [
                {
                    "text": (
                        "You are a helpful assistant for a study project. "
                        "Answer in the user's language and keep the response concise."
                    )
                }
            ]
        },
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": 256,
            "temperature": 0.2,
            "thinkingConfig": {
                "thinkingBudget": 0,
            },
        },
    }

    model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    req = request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            raw_body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8")
        raise RuntimeError(f"Gemini request failed: {raw_body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Gemini request failed: {exc.reason}") from exc

    try:
        body: Dict[str, Any] = json.loads(raw_body)
        return body["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Gemini response parsing failed: {raw_body}") from exc
