import unicodedata

from timelength.enums import CharacterType, StringType


def is_int(num: str) -> bool:
    """Check if the passed string is an integer."""
    try:
        num_int = int(num)
        return num_int == float(num)
    except ValueError:
        return False


def is_float(num: str) -> bool:
    """Check if the passed string is a number."""
    try:
        float(num)
        return True
    except ValueError:
        return False


def character_type(text: str) -> CharacterType:
    """Check the type of character based on the `CharacterType` enum."""
    if is_float(text):
        return CharacterType.NUMBER
    elif text.isalpha():
        return CharacterType.ALPHABET
    else:
        return CharacterType.SPECIAL


def string_type(text: str, scales: list, numerals: list, symbols: list) -> StringType:
    """Check the type of string based on the `StringType` enum."""
    if is_float(text):
        return StringType.NUMBER
    elif text in scales:
        return StringType.SCALE
    elif text in numerals:
        return StringType.NUMERAL
    elif text in symbols:
        return StringType.SPECIAL
    else:
        return StringType.UNKNOWN


def remove_diacritics(text: str) -> str:
    """Replace accented and special characters with their normalized equivalents."""
    nfkd_form = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])
