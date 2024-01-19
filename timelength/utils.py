import unicodedata

from timelength.enums import BufferType, CharacterType


def is_float(num: str):
    try:
        float(num)
        return True
    except ValueError:
        return False


def character_type(text: str):
    if is_float(text):
        return CharacterType.FLOAT
    elif text.isalpha():
        return CharacterType.ALPHABET
    else:
        return CharacterType.SPECIAL


def buffer_type(text: str, scales: list, numerals: list, defined_symbols: list):
    if is_float(text):
        return BufferType.FLOAT
    elif text in scales:
        return BufferType.SCALE
    elif text in numerals:
        return BufferType.NUMERAL
    elif text in defined_symbols:
        return BufferType.SPECIAL
    else:
        return BufferType.UNKNOWN


def remove_diacritics(text: str):
    nfkd_form = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])
