from dataclasses import dataclass, field


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

    - `__bool__`: Return `False` if all values are default, `True` otherwise.
    - `__str__`: Return a string indicating the success or failure of the parsing.
    - `__repr__`: Return a string representation of the `ParsedTimeLength` with attributes included.
    """

    success: bool = False
    seconds: float = 0.0
    invalid: list = field(default_factory=list)
    valid: list = field(default_factory=list)

    def __bool__(self) -> bool:
        """Return `False` if all values are default, `True` otherwise."""
        return self.success or self.seconds != 0.0 or self.invalid or self.valid

    def __str__(self):
        """Return a string indicating the success or failure of the parsing."""
        return "Success" if self.success else "Failure"

    def __repr__(self):
        """Return a string representation of the `ParsedTimeLength` with attributes included."""
        return f"ParsedTimeLength({self.success}, {self.seconds}, {self.invalid}, {self.valid})"


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
        return self.singular

    def __repr__(self):
        """Return a string representation of the Scale with attributes included."""
        return f'Scale({self.scale}, "{self.singular}", "{self.plural}")'
