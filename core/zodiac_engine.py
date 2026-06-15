"""Stub zodiac engine — prevents ImportError in main.py during test collection."""
from __future__ import annotations

ALL_SIGNS: list[str] = [
    "aries","taurus","gemini","cancer","leo","virgo",
    "libra","scorpio","sagittarius","capricorn","aquarius","pisces",
]

ZODIAC_FORM_MAP: dict[str, str] = {s: s.capitalize() for s in ALL_SIGNS}


class ZodiacEngine:
    def get_sign(self, birth_date: str) -> str:
        return "unknown"

    def get_form(self, sign: str) -> str:
        return ZODIAC_FORM_MAP.get(sign, "Unknown")
