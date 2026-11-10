import json
import re


def parse_json_object(text: str) -> dict:
    """Parse a JSON object, including responses wrapped in markdown fences."""
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("Model did not return a JSON object") from None
        try:
            value = json.loads(raw[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError("Model did not return a JSON object") from exc
    if not isinstance(value, dict):
        raise ValueError("Model JSON must be an object")
    return value


def strip_fences(text: str) -> str:
    raw = text.strip()
    match = re.match(r"^```(?:markdown|md)?\s*([\s\S]*?)\s*```$", raw)
    if match:
        return match.group(1).strip()
    return raw
