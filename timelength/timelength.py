from timelength.dataclasses import ParsedTimeLength
from timelength.errors import DisabledScale
from timelength.locales import English, Locale


class TimeLength:
    """A length of time.

    Represents a length of time provided in a human readable format.

    ### Attributes

    - `content` (`str`): The string content representing the length of time.
    - `strict` (`bool`): Determines the strictness of the parsing process. If `True`,
        only strictly formatted time strings are accepted with invalid inputs causing errors. 
        Strictness is somewhat arbitrary and based on decisions made about expectations from the 
        specified Locale, and as such may vary in its behavior between Locales. Defaults to `False`.
        If a middleground is desired, it is recommended to set `strict` to `False` and to manually
        check `TimeLength.result.invalid` after parsing.
    - `locale` (`Locale`): The locale context used for parsing the time string. Defaults to English.
    - `result` (`ParsedTimeLength`): The result of the parsing.

    ### Methods

    - `parse()`: Parses the `content` attribute based on the specified strictness and locale.
        Automatically called during initialization. Manually call this method again if changes
        are made to strictness or locale.
    - Conversion methods (`to_milliseconds`, `to_seconds`, `to_minutes`, `to_hours`, `to_days`,
        `to_weeks`, `to_months`, `to_years`, `to_decades`, `to_centuries`) return the total duration
        in their respective units with the specified precision.

    ### Example

    ```python
    time_length = TimeLength("2 hours 30 minutes")
    if time_length.success:
        print(f"Total seconds: {time_length.total_seconds}")
    ```
    """

    def __init__(
        self, content: str = "", strict: bool = False, locale: Locale = English()
    ) -> None:
        """Initialize the `TimeLength` based on passed settings and call the `parse` method."""
        self.content = content
        self.strict = strict
        self.locale = locale
        self.result = ParsedTimeLength()
        self._init_parse = True
        self.parse()

    def __str__(self) -> str:
        return f"<TimeLength \"{self.content[:50] + '...' if len(self.content) > 50 else self.content}\">"

    def __repr__(self) -> str:
        return self.__str__()

    def parse(self) -> None:
        """Parse the passed content using the parser attached to the object's `Locale`."""
        if (
            hasattr(self.locale, "_parser")
            and self.locale._parser
            and callable(self.locale._parser)
        ):
            if not self._init_parse:
                self.result = ParsedTimeLength()
            else:
                self._init_parse = False
            self.locale._parser(self.content, self.strict, self.locale, self.result)

    def to_milliseconds(self, max_precision=2) -> int:
        '''Convert the total seconds to milliseconds.
        
        ### Args
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are 
        dropped during rounding. Defaults to `2`.
        '''
        return self._round(
            self.result.seconds, self.locale._millisecond.scale, max_precision
        )

    def to_seconds(self, max_precision=2) -> int:
        '''Convert the total seconds to seconds. Only useful if the seconds `Scale` has been modified.
        
        ### Args
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are 
        dropped during rounding. Defaults to `2`.
        '''
        return self._round(
            self.result.seconds, self.locale._second.scale, max_precision
        )

    def to_minutes(self, max_precision=2) -> int:
        '''Convert the total seconds to minutes.
        
        ### Args
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are 
        dropped during rounding. Defaults to `2`.
        '''
        return self._round(
            self.result.seconds, self.locale._minute.scale, max_precision
        )

    def to_hours(self, max_precision=2) -> int:
        '''Convert the total seconds to hours.
        
        ### Args
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are 
        dropped during rounding. Defaults to `2`.
        '''
        return self._round(self.result.seconds, self.locale._hour.scale, max_precision)

    def to_days(self, max_precision=2) -> int:
        '''Convert the total seconds to days.
        
        ### Args
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are 
        dropped during rounding. Defaults to `2`.
        '''
        return self._round(self.result.seconds, self.locale._day.scale, max_precision)

    def to_weeks(self, max_precision=2) -> int:
        '''Convert the total seconds to weeks.
        
        ### Args
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are 
        dropped during rounding. Defaults to `2`.
        '''
        return self._round(self.result.seconds, self.locale._week.scale, max_precision)

    def to_months(self, max_precision=2) -> int:
        '''Convert the total seconds to months.
        
        ### Args
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are 
        dropped during rounding. Defaults to `2`.
        '''
        return self._round(self.result.seconds, self.locale._month.scale, max_precision)

    def to_years(self, max_precision=2) -> int:
        '''Convert the total seconds to years.
        
        ### Args
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are 
        dropped during rounding. Defaults to `2`.
        '''
        return self._round(self.result.seconds, self.locale._year.scale, max_precision)

    def to_decades(self, max_precision=2) -> int:
        '''Convert the total seconds to decades.
        
        ### Args
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are 
        dropped during rounding. Defaults to `2`.
        '''
        return self._round(
            self.result.seconds, self.locale._decade.scale, max_precision
        )

    def to_centuries(self, max_precision=2) -> int:
        '''Convert the total seconds to centuries.
        
        ### Args
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are 
        dropped during rounding. Defaults to `2`.
        '''
        return self._round(
            self.result.seconds, self.locale._century.scale, max_precision
        )

    def _round(self, total_seconds: float, scale: float, max_precision: int) -> int:
        try:
            return round(total_seconds / scale, max_precision)
        except ZeroDivisionError as e:
            raise DisabledScale(
                "That Scale has been disabled by being removed from the config."
            ) from e
