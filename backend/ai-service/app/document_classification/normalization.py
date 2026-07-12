from __future__ import annotations

import re
import unicodedata


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).upper()
    characters: list[str] = []
    for character in normalized:
        category = unicodedata.category(character)
        if category[0] in {"L", "N"}:
            characters.append(character)
        else:
            characters.append(" ")
    return re.sub(r"\s+", " ", "".join(characters)).strip()

