from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timedelta
from typing import Literal

from timelength.enums import FailureFlags, NumeralType


@dataclass
class Scale:
    """---
    Represents a time scale.

    #### Attributes
    - scale: `float = 0.0` — The number of seconds in the scale.
    - singular: `str = ""` — The singular form of the scale.
    - plural: `str = ""` — The plural form of the scale.
    - terms: `tuple[str, ...] = ()` — A tuple of terms associated with the scale.
    - enabled: `bool = True` — Whether the scale is enabled or not.

    #### Properties
    - valid: `bool` — Return whether the scale is valid or not based on all attributes being set.
    """

    scale: float = 0.0
    singular: str = ""
    plural: str = ""
    terms: tuple[str, ...] = ()
    enabled: bool = True

    @property
    def valid(self) -> bool:
        """Return whether the scale is valid or not based on all attributes being set."""
        return bool(self.scale and self.singular and self.plural and self.terms)

    def __str__(self) -> str:
        """Return the title cased singular form of the scale."""
        return self.singular.title()

    def __repr__(self) -> str:
        """Return a string representation of the scale with attributes included."""

        def tuple_to_str(tup: tuple) -> str:
            return "(" + ", ".join([json.dumps(term) for term in tup]) + ")"

        terms_str = tuple_to_str(self.terms)
        return f"Scale(scale={self.scale}, singular={json.dumps(self.singular)}, plural={json.dumps(self.plural)}, terms={terms_str}, enabled={self.enabled})"

    def __eq__(self, value: object) -> bool:
        """Return whether the scale is equal to the value."""
        if not isinstance(value, Scale):
            return False
        return self.scale == value.scale

    def __hash__(self) -> int:
        """Return the hash of the scale."""
        return hash((self.scale, self.singular, self.plural, self.terms, self.enabled))


@dataclass
class Numeral:
    """---
    Represents a number related word.

    #### Attributes
    - name: `str = ""` — The name of the numeral.
    - type: `NumeralType = NumeralType.NONE` — The type of numeral.
    - value: `float = 0.0` — The value of the numeral.
    - terms: `tuple[str, ...] = []` — A list of terms associated with the numeral.

    #### Properties
    - valid: `bool` — Return whether the numeral is valid or not based on all attributes being set.
    """

    name: str = ""
    type: NumeralType = NumeralType.NONE
    value: float = 0.0
    terms: tuple[str, ...] = ()
    enabled: bool = True

    @property
    def valid(self) -> bool:
        """Return whether the numeral is valid or not based on all attributes being set."""
        return bool(
            self.name and self.type and self.type is not NumeralType.NONE and self.value is not None and self.terms
        )

    def __str__(self) -> str:
        """Return the title cased singular form of the numeral."""
        return self.name.title()

    def __repr__(self) -> str:
        """Return a string representation of the numeral with attributes included."""

        def tuple_to_str(tup: tuple) -> str:
            return "(" + ", ".join([json.dumps(term) for term in tup]) + ")"

        terms_str = tuple_to_str(self.terms)
        return f"Numeral(name={json.dumps(self.name)}, type={self.type}, value={self.value}, terms={terms_str}, enabled={self.enabled})"

    def __eq__(self, value: object) -> bool:
        """Return whether the numeral is equal to the value."""
        if not isinstance(value, Numeral):
            return False
        return self.value == value.value

    def __hash__(self) -> int:
        """Return the hash of the numeral."""
        return hash((self.name, self.type, self.value, self.terms, self.enabled))


class ParsedTimeLength:
    """
    Represents the outcome of parsing a TimeLength.

    #### Properties
    - success: `str` — Indicates if the parsing was successful.
    - seconds: `float` — The total length of time parsed, in seconds.
    - delta: `timedelta | None` — The parsed time as a `timedelta`, or `None` if out of range.
    - invalid: `tuple` — The parts of the input string that could not be parsed as valid time.
    - valid: `tuple` — The parts of the input string that were successfully parsed as valid time.
    """

    def __init__(
        self,
        success: bool = False,
        seconds: float = 0.0,
        delta: timedelta | None = None,
        invalid: tuple[tuple[float | str, FailureFlags], ...] = (),
        valid: tuple[tuple[float, Scale], ...] = (),
    ) -> None:
        self._success: bool = success
        self._seconds: float = seconds
        self._delta: timedelta | None = delta
        self._invalid: tuple[tuple[float | str, FailureFlags], ...] = invalid
        self._valid: tuple[tuple[float, Scale], ...] = valid

    @property
    def success(self) -> bool:
        """Return if the parsing was successful."""
        return self._success

    @property
    def seconds(self) -> float:
        """Return the total length of time parsed, in seconds."""
        return self._seconds

    @property
    def delta(self) -> timedelta | None:
        """Return a timedelta representing the parsed time, or None if out of range."""
        return self._delta

    @property
    def invalid(self) -> tuple[tuple[float | str, FailureFlags], ...]:
        """Return a tuple of parts of the input string that could not be parsed as valid time."""
        return self._invalid

    @property
    def valid(self) -> tuple[tuple[float, Scale], ...]:
        """Return a tuple of parts of the input string that were successfully parsed as valid time."""
        return self._valid

    def __str__(self) -> str:
        """Return a string indicating the success or failure of the parsing."""
        return "Success" if self.success else "Failure"

    def __repr__(self) -> str:
        """Return a string representation of the ParsedTimeLength with attributes included."""

        def tuple_to_str(tup: tuple) -> str:
            return (
                "("
                + ", ".join(
                    [
                        tuple_to_str(term)
                        if isinstance(term, tuple)
                        else repr(term)
                        if isinstance(term, Scale)
                        else json.dumps(term)
                        for term in tup
                    ]
                )
                + ")"
            )

        valid_str = tuple_to_str(self.valid)
        invalid_str = tuple_to_str(self.invalid)
        return f"ParsedTimeLength(success={self.success}, seconds={self.seconds}, invalid={invalid_str}, valid={valid_str})"


@dataclass
class Buffer:
    """---
    Represents the state of the buffer during parsing.

    #### Attributes
    - value: `str = ""` — The current value of the buffer.
    """

    value: str = ""

    def __str__(self) -> str:
        """Return the current value of the buffer."""
        return self.value

    def __repr__(self) -> str:
        """Return a string representation of the buffer with attributes included."""
        return f'Buffer(value="{self.value}")'


@dataclass
class ParserSettings:
    """---
    Represents the settings for the parser.

    #### Attributes
    - assume_scale: `Literal["LAST", "SINGLE", "NEVER"] = "SINGLE"` — How to handle no scale being provided.
        - `LAST` will assume seconds only for the last value if no scale is provided for it.
        - `SINGLE` will only assume seconds when a single input is provided.
        - `NEVER` will never assume seconds when no scale is provided.
    - limit_allowed_terms: `bool = True` — Prevent terms from the `allowed_terms` list in
        the config from being used in the middle of a segment, thus interrupting a value/scale pair.
        - The affected segment will become abandoned and added to the invalid list.
        - The terms may still be used at the beginning or end of a segment/sentence.
        - If `False`, The terms will be ignored (within other limitations) and not effect parsing.
    - allow_duplicate_scales: `bool = True` — Allow scales to be parsed multiple times, stacking their values.
        - If `False`, the first scale will be used and subsequent duplicates will be added to the invalid list.
    - allow_thousands_extra_digits: `bool = False` — Allow thousands to be parsed with more than three digits
        following the thousand delimiter.
        - Ex: `1,2345` will be interpreted as `12,345`.
    - allow_thousands_lacking_digits: `bool = False` — Allow thousands to be parsed with less than three digits.
        - Ex: `1,23` will be interpreted as `123`.
    - allow_decimals_lacking_digits: `bool = True` — Allow decimals to be parsed with no number following the
        decimal delimiter.
        - Ex: `1.` will be interpreted as `1.0`.
    """

    assume_scale: Literal["LAST", "SINGLE", "NEVER"] = "SINGLE"
    limit_allowed_terms: bool = True
    allow_duplicate_scales: bool = True
    allow_thousands_extra_digits: bool = False
    allow_thousands_lacking_digits: bool = False
    allow_decimals_lacking_digits: bool = True

    def __str__(self) -> str:
        """Return the settings as either 'Default' or 'Modified' based on the default values."""
        return (
            "Modified"
            if any(
                [
                    self.assume_scale != "SINGLE",
                    self.limit_allowed_terms is False,
                    self.allow_duplicate_scales is False,
                    self.allow_thousands_extra_digits is True,
                    self.allow_thousands_lacking_digits is True,
                    self.allow_decimals_lacking_digits is False,
                ]
            )
            else "Default"
        )

    def __repr__(self) -> str:
        """Return a string representation of the ParserSettings with attributes included."""
        return (
            f'ParserSettings(assume_scale="{self.assume_scale}", '
            + f"limit_allowed_terms={self.limit_allowed_terms}, "
            + f"allow_duplicate_scales={self.allow_duplicate_scales}, "
            + f"allow_thousands_extra_digits={self.allow_thousands_extra_digits}, "
            + f"allow_thousands_lacking_digits={self.allow_thousands_lacking_digits}, "
            + f"allow_decimals_lacking_digits={self.allow_decimals_lacking_digits})"
        )
