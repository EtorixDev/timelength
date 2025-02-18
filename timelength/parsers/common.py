from __future__ import annotations

import unicodedata

from timelength.enums import CharacterType, ValueType


def is_int(num: str | int | float) -> bool:
    """Check if the passed string is an integer."""
    try:
        num_int = int(float(num))
        return num_int == float(num)
    except ValueError:
        return False


def is_number(num: str) -> bool:
    """Check if the passed string is a number."""
    try:
        float(num)
        return True
    except ValueError:
        return False


def character_type(text: str) -> CharacterType:
    """Check the type of character based on the `CharacterType` enum."""
    if is_number(text):
        return CharacterType.NUMBER
    elif text.isalpha():
        return CharacterType.ALPHABET
    else:
        return CharacterType.SYMBOL


def value_type(text: str, scale_terms: list, numeral_terms: list, symbol_terms: list) -> ValueType:
    """Check the type of string based on the `ValueType` enum."""
    if is_number(text):
        return ValueType.NUMBER
    elif text in scale_terms:
        return ValueType.SCALE
    elif text in numeral_terms:
        return ValueType.NUMERAL
    elif text in symbol_terms:
        return ValueType.SYMBOL
    else:
        return ValueType.MIXED


def remove_diacritics(text: str) -> str:
    """Replace accented and special characters with their normalized equivalents."""
    nfkd_form = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])
