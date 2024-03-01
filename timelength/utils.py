import unicodedata

from timelength.enums import BufferType, CharacterType


def is_float(num: str):
    '''Check if the passed string is a number.'''
    try:
        float(num)
        return True
    except ValueError:
        return False


def character_type(text: str):
    '''Check the type of the passed character based on the `CharacterType` enum.'''
    if is_float(text):
        return CharacterType.NUMBER
    elif text.isalpha():
        return CharacterType.ALPHABET
    else:
        return CharacterType.SPECIAL


def buffer_type(text: str, scales: list, numerals: list, symbols: list):
    '''Check the type of the passed string based on the `BufferType` enum.'''
    if is_float(text):
        return BufferType.NUMBER
    elif text in scales:
        return BufferType.SCALE
    elif text in numerals:
        return BufferType.NUMERAL
    elif text in symbols:
        return BufferType.SPECIAL
    else:
        return BufferType.UNKNOWN


def remove_diacritics(text: str):
    '''Replace accented and special characters with their normalized equivalents.'''
    nfkd_form = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])
