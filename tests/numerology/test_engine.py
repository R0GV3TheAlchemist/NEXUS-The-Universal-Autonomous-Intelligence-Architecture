import pytest
from datetime import date
from gaia.numerology.engine import (
    reduce_to_single,
    calc_life_path,
    calc_expression,
    calc_soul_urge,
    calc_personality,
    calc_birthday,
    normalize_name,
)


def test_reduce_basic_master_preserved():
    val, path = reduce_to_single(29, use_master_numbers=True)
    assert val == 11
    assert 11 in path


def test_reduce_master_not_preserved():
    val, _ = reduce_to_single(29, use_master_numbers=False)
    assert val == 2  # 11 -> 1+1 -> 2


def test_reduce_single_digit_unchanged():
    val, path = reduce_to_single(7)
    assert val == 7
    assert path == [7]


def test_reduce_22_preserved():
    val, _ = reduce_to_single(22, use_master_numbers=True)
    assert val == 22


def test_reduce_33_preserved():
    val, _ = reduce_to_single(33, use_master_numbers=True)
    assert val == 33


def test_life_path_kyle_steen():
    # July 2, 1993: m=7(7), d=2(2), y=1+9+9+3=22(master) -> 7+2+22=31 -> 3+1=4
    result = calc_life_path(date(1993, 7, 2), use_master_numbers=True)
    assert result["reduced_value"] == 4


def test_normalize_name_strips_punctuation():
    assert normalize_name("Kyle  Steen") == "KYLE STEEN"
    assert normalize_name("O'Brien") == "OBRIEN"


def test_expression_deterministic():
    r1 = calc_expression("Kyle Steen", True)
    r2 = calc_expression("Kyle Steen", True)
    assert r1 == r2


def test_soul_urge_vowels_within_range():
    result = calc_soul_urge("Kyle Steen", True, "standard")
    assert result["reduced_value"] in list(range(1, 10)) + [11, 22, 33]


def test_personality_consonants_within_range():
    result = calc_personality("Kyle Steen", True, "standard")
    assert result["reduced_value"] in list(range(1, 10)) + [11, 22, 33]


def test_birthday_no_master():
    result = calc_birthday(date(1993, 7, 2))
    assert result["reduced_value"] == 2
    assert result["is_master_number"] is False


def test_birthday_day_11_not_master():
    result = calc_birthday(date(1993, 7, 11))
    assert result["reduced_value"] == 2  # 11 -> 2 (no master exception for birthday)
    assert result["is_master_number"] is False


def test_soul_urge_y_as_vowel_differs():
    r_standard = calc_soul_urge("Kyle", True, "standard")
    r_y_vowel  = calc_soul_urge("Kyle", True, "y-as-vowel")
    # Y treated as vowel in y-as-vowel mode, so raw values should differ
    assert r_standard["raw_value"] != r_y_vowel["raw_value"]
