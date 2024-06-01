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


class NumeralType(Enum):
    """
    Enumerates the types of numerals recognized during parsing.
    
    ### Members
    - `DIGIT`: Represents digit numerals (ex: one).
    - `TEEN`: Represents teen numerals (ex: eleven).
    - `TEN`: Represents ten numerals (ex: twenty).
    - `HUNDRED`: Represents hundred numerals (ex: hundred).
    - `THOUSAND`: Represents thousand numerals (ex: thousand).
    - `MODIFIER`: Represents modifier numerals (ex: half).
    - `MULTIPLIER`: Represents multipliers numerals (ex: of).
    """

    DIGIT = "DIGIT"
    TEEN = "TEEN"
    TEN = "TEN"
    HUNDRED = "HUNDRED"
    THOUSAND = "THOUSAND"
    MODIFIER = "MODIFIER"
    MULTIPLIER = "MULTIPLIER"
