import re


def normalize_text(value: str) -> str:
    collapsed = re.sub(r"\s+", " ", value)
    return collapsed.strip()


def trim_to_chars(value: str, limit: int) -> str:
    normalized = normalize_text(value)
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def language_name(language: str) -> str:
    return "French" if language == "fr" else "English"