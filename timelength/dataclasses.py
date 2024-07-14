from dataclasses import dataclass, field
from typing import Literal

from timelength.enums import FailureFlags


@dataclass
class Scale:
    """
    Represents a scale for converting units of time.

    ### Attributes

    - `scale` (`float`): Approximately how many seconds this `Scale` is equivalent to.
    - `singular` (`str`): The singular form of the `Scale`'s name.
    - `plural` (`str`): The plural form of the `Scale`'s name.
    - `terms` (`list`): A list of abbreviations associated with the `Scale`.

    ### Methods

    - `__str__`: Returns the singular form of the Scale.
    - `__repr__`: Returns a string representation of the Scale with attributes included.
    """

    scale: float = 0.0
    singular: str = ""
    plural: str = ""
    terms: list = field(default_factory=list)

    def __str__(self):
        """Return the singular form of the Scale."""
        return self.singular.title()

    def __repr__(self):
        """Return a string representation of the Scale with attributes included."""
        return f'Scale({self.scale}, "{self.singular}", "{self.plural}")'

    def __bool__(self):
        """Return if the Scale is enabled or not."""
        return bool(self.scale)


@dataclass
class ParsedTimeLength:
    """
    Represents the outcome of parsing a length of time from a string.

    ### Attributes

    - `success` (`bool`): Indicates if the parsing was successful.
    - `seconds` (`float`): The total length of time parsed, in seconds.
    - `invalid` (`list`): A list of parts of the input string that could not be parsed as valid time.
    - `valid` (`list`): A list of parts of the input string that were successfully parsed as valid time.

    ### Methods

    - `__str__`: Return a string indicating the success or failure of the parsing.
    - `__repr__`: Return a string representation of the `ParsedTimeLength` with attributes included.
    """

    success: bool = False
    seconds: float = 0.0
    invalid: list[tuple[float | str, FailureFlags]] = field(default_factory=list)
    valid: list[tuple[float, Scale]] = field(default_factory=list)

    def __str__(self):
        """Return a string indicating the success or failure of the parsing."""
        return "Success" if self.success else "Failure"

    def __repr__(self):
        """Return a string representation of the `ParsedTimeLength` with attributes included."""
        return f"ParsedTimeLength(success={self.success}, seconds={self.seconds}, invalid={self.invalid}, valid={self.valid})"


@dataclass
class Buffer:
    """
    Represents the state of the buffer during parsing.

    ### Attributes
    - `value` (`str`): The current value of the buffer.

    ### Methods
    - `__str__`: Return the value of the buffer as a string.
    - `__repr__`: Return a string representation of the `Buffer` with attributes included.
    """

    value: str = ""

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f'Buffer(value="{self.value}")'

    def __add__(self, other: str) -> str:
        return self.value + other

    def __radd__(self, other: str) -> str:
        return other + self.value

    def __bool__(self) -> bool:
        return bool(self.value)


@dataclass
class ParserSettings:
    """
    Represents the settings for the parser.

    ### Attributes
    - `assume_seconds` (`Literal["LAST", "SINGLE", "NEVER"]`): Defaults to `SINGLE`. How to handle no scale being
        provided. If seconds are disabled, the first loaded scale will take its place.
        - `LAST`: Assume seconds only for the last value if no scale is provided for it.
        - `SINGLE`: Only assume seconds when a single number is provided.
        - `NEVER`: Never assume seconds when no scale is provided.
    - `limit_allowed_terms` (`bool`): Defaults to `True`. Prevent terms from the `allowed_terms` list in the config
        from being used in the middle of a segment/sentence, thus interrupting a value/scale pair. The affected segment
        will become abandoned and added to the invalid list. The terms may still be used at the beginning or end of a
        segment/sentence. If `False`, The terms will be ignored (within other limitations) and not effect parsing.
    - `allow_duplicate_scales` (`bool`): Defaults to `True`. Allow scales to be parsed multiple times. The values will
        stack. If `False`, the first scale will be used and subsequent duplicates will be added to the invalid list.
    - `allow_thousands_extra_digits` (`bool`): Defaults to `False`. If `True`, allow thousands to be parsed with more
        than three digits following the thousand delimiter. Ex: `1,2345` will be interpreted as `12,345`.
    - `allow_thousands_lacking_digits` (`bool`): Defaults to `False`. If `True`, allow thousands to be parsed with less
        than three digits following the thousand delimiter. Ex: `1,23` will be interpreted as `123`.
    - `allow_decimals_lacking_digits` (`bool`): Defaults to `True`. Allow decimals to be parsed with no number following
        the decimal delimiter. Ex: `1.` will be interpreted as `1.0`. If `False`, the number will be added to the invalid list.

    ### Methods
    - `__str__`: Return whether the settings were modified or not as a string.
    - `__repr__`: Return a string representation of the `ParserSettings` with attributes included.
    """

    assume_seconds: Literal["LAST", "SINGLE", "NEVER"] = "SINGLE"
    limit_allowed_terms: bool = True
    allow_duplicate_scales: bool = True
    allow_thousands_extra_digits: bool = False
    allow_thousands_lacking_digits: bool = False
    allow_decimals_lacking_digits: bool = True

    def __str__(self):
        return (
            "Modified"
            if any(
                [
                    self.assume_seconds != "SINGLE",
                    not self.limit_allowed_terms,
                    not self.allow_duplicate_scales,
                    self.allow_thousands_extra_digits,
                    self.allow_thousands_lacking_digits,
                    not self.allow_decimals_lacking_digits,
                ]
            )
            else "Default"
        )

    def __repr__(self):
        return f'ParserSettings(assume_seconds="{self.assume_seconds}", limit_allowed_terms={self.limit_allowed_terms}, allow_duplicate_scales={self.allow_duplicate_scales}, allow_thousands_extra_digits={self.allow_thousands_extra_digits}, allow_thousands_lacking_digits={self.allow_thousands_lacking_digits}, allow_decimals_lacking_digits={self.allow_decimals_lacking_digits})'
