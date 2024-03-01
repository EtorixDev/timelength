from enum import Enum


class CharacterType(Enum):
    """
    Enumerates the types of characters recognized during parsing.

    ### Members
    - `NUMBER`: Represents number characters.
    - `ALPHABET`: Represents alphabetic characters.
    - `SPECIAL`: Represents special characters (ex: !).
    """
    NUMBER = "NUMBER"
    ALPHABET = "ALPHABET"
    SPECIAL = "SPECIAL"


class BufferType(Enum):
    """
    Enumerates the types of buffers recognized during parsing.

    ### Members
    - `NUMBER`: Represents number strings.
    - `SCALE`: Represents scale strings (ex: minutes).
    - `NUMERAL`: Represents numeral strings (ex: twenty).
    - `SPECIAL`: Represents special strings (ex: !$^).
    - `UNKNOWN`: Represents other uncategorizable strings.
    """
    NUMBER = "NUMBER"
    SCALE = "SCALE"
    NUMERAL = "NUMERAL"
    SPECIAL = "SPECIAL"
    UNKNOWN = "UNKNOWN"
