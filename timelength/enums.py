from enum import Enum


class CharacterType(Enum):
    FLOAT = "FLOAT"
    ALPHABET = "ALPHABET"
    SPECIAL = "SPECIAL"


class BufferType(Enum):
    FLOAT = "FLOAT"
    SCALE = "SCALE"
    NUMERAL = "NUMERAL"
    SPECIAL = "SPECIAL"
    UNKNOWN = "UNKNOWN"
