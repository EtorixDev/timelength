from enum import Enum, IntFlag, auto


class CharacterType(Enum):
    """
    Represents the types of characters recognized during parsing.

    ### Members
    - `NUMBER`: Represents number characters.
    - `ALPHABET`: Represents alphabetic characters.
    - `SPECIAL`: Represents special characters (ex: !).
    """

    NUMBER = "NUMBER"
    ALPHABET = "ALPHABET"
    SPECIAL = "SPECIAL"


class StringType(Enum):
    """
    Represents the types of buffers recognized during parsing.

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
    Represents the types of numerals recognized during parsing.

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


class FailureFlags(IntFlag):
    """
    Represents the things which will cause parsing to fail.

    ### Methods
    - `__str__`: Return the names of the enabled flags.
    - `__repr__`: Return a string representation of the enabled flags.

    ### Members
    - `NONE`: No failures will cause parsing to fail.
    - `ALL`: Any failure will cause parsing to fail.
    - `MALFORMED_CONTENT`: The fallback when something that shouldn't have happened, happened.
    - `UNKNOWN_TERM`: The parsed value was not recognized from the terms or symbols in the config.
    - `MALFORMED_DECIMAL`: Multiple decimals were attempted within a singular decimal segment.
    - `MALFORMED_THOUSAND`: A thousand segment was attempted but did not have a leading number or three digits following a thousand separator.
    - `MALFORMED_HHMMSS`: The input for HH:MM:SS either had more segments than enabled scales, or was not formatted correctly.
    - `LONELY_VALUE`: A value was parsed with no paired scale.
    - `CONSECUTIVE_VALUE`: Multiple values were parsed in a row with no scales in between.
    - `LONELY_SCALE`: A scale was parsed with no paired value.
    - `LEADING_SCALE`: A scale was parsed at the beginning of the input.
    - `DUPLICATE_SCALE`: A scale was parsed multiple times.
    - `CONSECUTIVE_SCALE`: Multiple scales were parsed in a row with no values in between.
    - `CONSECUTIVE_CONNECTOR`: More than 2 connectors were parsed in a row.
    - `CONSECUTIVE_SEGMENTORS`: Multiple segmentors were parsed in a row.
    - `CONSECUTIVE_SPECIALS`: Multiple special characters/phrases were parsed in a row.
    - `MISPLACED_ALLOWED_TERM`: A member of the `allowed_terms` list was found in the middle of a segment/sentence.
    - `UNUSED_MULTIPLIER`: A term of the multiplier numeral was parsed but unused on any values.
    """

    NONE = 0
    MALFORMED_CONTENT = auto()
    UNKNOWN_TERM = auto()
    MALFORMED_DECIMAL = auto()
    MALFORMED_THOUSAND = auto()
    MALFORMED_HHMMSS = auto()
    LONELY_VALUE = auto()
    CONSECUTIVE_VALUE = auto()
    LONELY_SCALE = auto()
    LEADING_SCALE = auto()
    DUPLICATE_SCALE = auto()
    CONSECUTIVE_SCALE = auto()
    CONSECUTIVE_CONNECTOR = auto()
    CONSECUTIVE_SEGMENTOR = auto()
    CONSECUTIVE_SPECIAL = auto()
    MISPLACED_ALLOWED_TERM = auto()
    UNUSED_MULTIPLIER = auto()
    ALL = (
        MALFORMED_CONTENT
        | UNKNOWN_TERM
        | MALFORMED_DECIMAL
        | MALFORMED_THOUSAND
        | MALFORMED_HHMMSS
        | LONELY_VALUE
        | CONSECUTIVE_VALUE
        | LONELY_SCALE
        | LEADING_SCALE
        | DUPLICATE_SCALE
        | CONSECUTIVE_SCALE
        | CONSECUTIVE_CONNECTOR
        | CONSECUTIVE_SEGMENTOR
        | CONSECUTIVE_SPECIAL
        | MISPLACED_ALLOWED_TERM
        | UNUSED_MULTIPLIER
    )

    def __str__(self) -> str:
        return self._name_.replace("|", " | ")

    def __repr__(self) -> str:
        return " | ".join([f"FailureFlags.{flag._name_}" for flag in self]) or "FailureFlags.NONE"
