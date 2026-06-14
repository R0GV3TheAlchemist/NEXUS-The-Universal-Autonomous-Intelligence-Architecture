"""Pure, stateless reduction functions — no side effects, fully testable."""
from __future__ import annotations
from datetime import date
from .constants import MASTER_NUMBERS, LETTER_MAP, VOWELS, VOWELS_Y


def digit_sum(n: int) -> int:
    return sum(int(d) for d in str(abs(n)))


def reduce_to_single(
    n: int,
    use_master_numbers: bool = True,
    path: list[int] | None = None,
) -> tuple[int, list[int]]:
    """
    Reduce n to a single digit (1-9), preserving 11, 22, 33 if use_master_numbers.
    Returns (reduced_value, reduction_path).
    """
    if path is None:
        path = [n]
    if n <= 9:
        return n, path
    if use_master_numbers and n in MASTER_NUMBERS:
        return n, path
    s = digit_sum(n)
    path.append(s)
    return reduce_to_single(s, use_master_numbers, path)


def build_core_number(raw: int, use_master_numbers: bool) -> dict:
    reduced, path = reduce_to_single(raw, use_master_numbers)
    return {
        "raw_value": raw,
        "reduced_value": reduced,
        "is_master_number": reduced in MASTER_NUMBERS,
        "reduction_path": path,
    }


def normalize_name(name: str) -> str:
    """Uppercase and strip non-alpha except spaces."""
    return "".join(c.upper() for c in name if c.isalpha() or c == " ").strip()


def letters_to_number(letters: str, use_master_numbers: bool) -> dict:
    raw = sum(LETTER_MAP.get(c, 0) for c in letters if c != " ")
    return build_core_number(raw, use_master_numbers)


def calc_life_path(birth_date: date, use_master_numbers: bool) -> dict:
    """
    Reduce month, day, and year independently, then sum and reduce the total.
    """
    m_val, _ = reduce_to_single(digit_sum(birth_date.month), use_master_numbers)
    d_val, _ = reduce_to_single(digit_sum(birth_date.day), use_master_numbers)
    y_val, _ = reduce_to_single(digit_sum(birth_date.year), use_master_numbers)
    raw = m_val + d_val + y_val
    return build_core_number(raw, use_master_numbers)


def calc_expression(name: str, use_master_numbers: bool) -> dict:
    norm = normalize_name(name)
    return letters_to_number(norm, use_master_numbers)


def calc_soul_urge(name: str, use_master_numbers: bool, vowel_mode: str) -> dict:
    norm = normalize_name(name)
    vowel_set = VOWELS_Y if vowel_mode == "y-as-vowel" else VOWELS
    vowels_only = "".join(c for c in norm if c in vowel_set)
    return letters_to_number(vowels_only, use_master_numbers)


def calc_personality(name: str, use_master_numbers: bool, vowel_mode: str) -> dict:
    norm = normalize_name(name)
    vowel_set = VOWELS_Y if vowel_mode == "y-as-vowel" else VOWELS
    consonants_only = "".join(c for c in norm if c.isalpha() and c not in vowel_set)
    return letters_to_number(consonants_only, use_master_numbers)


def calc_birthday(birth_date: date) -> dict:
    """Day number reduced to single digit — no master number exception."""
    raw = birth_date.day
    reduced, path = reduce_to_single(raw, use_master_numbers=False)
    return {
        "raw_value": raw,
        "reduced_value": reduced,
        "is_master_number": False,
        "reduction_path": path,
    }
