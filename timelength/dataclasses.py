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

    - `__str__`: Return a string indicating the success or failure of the parsing.
    - `__repr__`: Return a string representation of the ParsedTimeLength with attributes included.
    """

    success: bool = False
    seconds: float = 0
    invalid: list = field(default_factory=list)
    valid: list = field(default_factory=list)

    def __str__(self):
        '''Return a string indicating the success or failure of the parsing.'''
        return "Success" if self.success else "Failure"

    def __repr__(self):
        '''Return a string representation of the ParsedTimeLength with attributes included.'''
        return f"ParsedTimeLength({self.success}, {self.seconds}, {self.invalid}, {self.valid})"


@dataclass
class Scale:
    """
    Represents a scale for converting units of time.

    ### Attributes

    - `scale` (`float`): The multiplier used to convert to the base unit (e.g., seconds). Defaults to `0`.
    - `singular` (`str`): The singular form of the unit's name. Defaults to an empty string.
    - `plural` (`str`): The plural form of the unit's name. Defaults to an empty string.
    - `terms` (`list`): A list of terms or abbreviations associated with the unit. Defaults to an empty list.

    ### Methods

    - `__str__`: Return the singular form of the Scale.
    - `__repr__`: Return a string representation of the Scale with attributes included.
    """

    scale: float = 0
    singular: str = ""
    plural: str = ""
    terms: list = field(default_factory=list)

    def __str__(self):
        '''Return the singular form of the Scale.'''
        return self.singular

    def __repr__(self):
        '''Return a string representation of the Scale with attributes included.'''
        return f"Scale({self.scale}, \"{self.singular}\", \"{self.plural}\", {self.terms})"
