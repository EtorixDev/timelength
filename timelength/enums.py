from enum import Enum, IntFlag, auto


class CharacterType(Enum):
    """
    Represents the types of characters recognized during parsing.

    #### Members
    - `NUMBER` — Represents number characters.
    - `ALPHABET` — Represents alphabetic characters.
    - `SYMBOL` — Represents symbol characters.
    """

    NUMBER = "NUMBER"
    ALPHABET = "ALPHABET"
    SYMBOL = "SYMBOL"


class ValueType(Enum):
    """
    Represents the types of strings recognized during parsing.

    #### Members
    - `NUMBER` — Represents number strings (ex: 123).
    - `NUMERAL` — Represents numeral strings (ex: twenty).
    - `SCALE` — Represents scale strings (ex: minutes).
    - `SYMBOL` — Represents symbol strings (ex: !$^).
    - `MIXED` — Represents mixed strings.
    """

    NUMBER = "NUMBER"
    NUMERAL = "NUMERAL"
    SCALE = "SCALE"
    SYMBOL = "SYMBOL"
    MIXED = "MIXED"


class NumeralType(Enum):
    """
    Represents the types of numerals recognized during parsing.

    #### Members
    - `DIGIT` — Represents digit numerals (ex: one).
    - `TEEN` — Represents teen numerals (ex: eleven).
    - `TEN` — Represents ten numerals (ex: twenty).
    - `HUNDRED` — Represents hundred numerals (ex: hundred).
    - `THOUSAND` — Represents thousand numerals (ex: thousand).
    - `MULTIPLIER` — Represents multiplier numerals (ex: half).
    - `OPERATOR` — Represents operator numerals (ex: of).
    - `NONE` — Represents no numeral type.
    """

    DIGIT = "DIGIT"
    TEEN = "TEEN"
    TEN = "TEN"
    HUNDRED = "HUNDRED"
    THOUSAND = "THOUSAND"
    MULTIPLIER = "MULTIPLIER"
    OPERATOR = "OPERATOR"
    NONE = "NONE"


class FailureFlags(IntFlag):
    """
    Represents the inputs which will cause parsing to fail.

    #### Members
    - `NONE` — No failures will cause parsing to fail.
    - `ALL` — Any failure will cause parsing to fail.
    - `MALFORMED_CONTENT` — The fallback when something that shouldn't have happened, happened.
    - `UNKNOWN_TERM` — The parsed value was not recognized from the terms or symbols in the config.
    - `MALFORMED_DECIMAL` — Multiple decimals were attempted within a singular decimal segment.
    - `MALFORMED_THOUSAND` — A thousand segment was attempted but did not have a leading number or a proper number of digits following a thousand separator.
    - `MALFORMED_FRACTION` — A fraction was attempted but had more than 2 values, a missing value, or was not formatted correctly.
    - `MALFORMED_HHMMSS` — An HH:MM:SS was attempted but had more segments than enabled scales or was not formatted correctly.
    - `LONELY_VALUE` — A value was parsed with no paired scale.
    - `LONELY_SCALE` — A scale was parsed with no paired value.
    - `LEADING_SCALE` — A scale was parsed at the beginning of the input.
    - `DUPLICATE_SCALE` — The same scale was parsed multiple times.
    - `CONSECUTIVE_CONNECTOR` — More than the allowed number of connectors were parsed in a row.
    - `CONSECUTIVE_SEGMENTORS` — More than the allowed number of segmentors were parsed in a row.
    - `CONSECUTIVE_SPECIALS` — More than the allowed number of special characters were parsed in a row.
    - `MISPLACED_ALLOWED_TERM` — An allowed term was found in the middle of a segment/sentence.
    - `MISPLACED_SPECIAL` — A special character was found in the middle of a segment/sentence.
    - `UNUSED_OPERATOR` — A term of the operator numeral was parsed but unused on any values.
    - `AMBIGUOUS_MULTIPLIER` — More than one multiplier was parsed for a single segment which may be ambiguous.
    """

    NONE = 0
    MALFORMED_CONTENT = auto()
    UNKNOWN_TERM = auto()
    MALFORMED_DECIMAL = auto()
    MALFORMED_THOUSAND = auto()
    MALFORMED_FRACTION = auto()
    MALFORMED_HHMMSS = auto()
    LONELY_VALUE = auto()
    LONELY_SCALE = auto()
    DUPLICATE_SCALE = auto()
    CONSECUTIVE_CONNECTOR = auto()
    CONSECUTIVE_SEGMENTOR = auto()
    CONSECUTIVE_SPECIAL = auto()
    MISPLACED_ALLOWED_TERM = auto()
    MISPLACED_SPECIAL = auto()
    UNUSED_OPERATOR = auto()
    AMBIGUOUS_MULTIPLIER = auto()
    ALL = (
        MALFORMED_CONTENT
        | UNKNOWN_TERM
        | MALFORMED_DECIMAL
        | MALFORMED_THOUSAND
        | MALFORMED_FRACTION
        | MALFORMED_HHMMSS
        | LONELY_VALUE
        | LONELY_SCALE
        | DUPLICATE_SCALE
        | CONSECUTIVE_CONNECTOR
        | CONSECUTIVE_SEGMENTOR
        | CONSECUTIVE_SPECIAL
        | MISPLACED_ALLOWED_TERM
        | MISPLACED_SPECIAL
        | UNUSED_OPERATOR
        | AMBIGUOUS_MULTIPLIER
    )

    def _get_flags(self) -> list:
        return [f"FailureFlags.{flag._name_}" for flag in FailureFlags if flag and flag in self]

    def __str__(self) -> str:
        return " | ".join(self._get_flags()).replace("FailureFlags.", "") or "NONE"

    def __repr__(self) -> str:
        return "(" + (" | ".join(self._get_flags()) or "FailureFlags.NONE") + ")"
