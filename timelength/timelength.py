import typing

from timelength.dataclasses import ParsedTimeLength
from timelength.errors import DisabledScale, LocaleConfigError
from timelength.locales import English, Locale


class TimeLength:
    """
    Represents a length of time provided in a human readable format.

    ### Attributes

    - `content` (`str`): The string content representing the length of time.
    - `strict` (`bool`): If `True`, then `result.success` will only return `True` if `result.valid`
        is populated and `result.invalid` is not populated during parsing. If `False` (Default), then
        `result.success` will return `True` as long as `result.valid` has at least one item regardless
        of the state of `result.invalid` at the end of the parsing.
    - `locale` (`Locale`): The locale context used for parsing the time string. Defaults to `English`.
    - `result` (`ParsedTimeLength`): The result of the parsing.

    ### Methods

    - `parse`: Parse the `content` attribute based on the `strict` and `locale` attributes.
        Automatically called during initialization. Manually call this method again if changes
        are made to `content`, `strict`, or `locale`.
    - `to_milliseconds`, `to_seconds`, `to_minutes`, `to_hours`, `to_days`, `to_weeks`, `to_months`,
        `to_years`, `to_decades`, `to_centuries`: Convert the total duration to the respective
        units of each method with specified precision.
    - `__str__`: Return the parsed lengths of time.
    - `__repr__`: Return a string representation of the `TimeLength` with attributes included.

    ### Example

    ```python
    time_length = TimeLength("2 hours 30 minutes")
    if time_length.result.success:
        print(f"Total Seconds: {time_length.to_seconds()}")
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
        self.parse()

    def __str__(self) -> str:
        """Return the valid parsed lengths of time."""
        return str(self.result.valid)

    def __repr__(self) -> str:
        """Return a string representation of the `TimeLength` with attributes included."""
        return f'TimeLength("{self.content}", {self.strict}, {self.locale})'

    def parse(self) -> None:
        """Parse the passed content using the parser attached to the `TimeLength`'s `Locale`."""
        if (
            hasattr(self.locale, "_parser")
            and self.locale._parser
            and callable(self.locale._parser)
        ):
            self.result = ParsedTimeLength()
            self.locale._parser(self.content.strip(), self.strict, self.locale, self.result)
        else:
            raise LocaleConfigError(
                f"Parser function not found attached to {self.locale}."
            ) from None

    def to_milliseconds(self, max_precision=2) -> typing.Union[int, float]:
        """Convert the total seconds to milliseconds.

        ### Args:
        - `max_precision` (`Union[int, float]`): The maximum number of decimal places to show. The rest are
        dropped during rounding. Defaults to `2`.

        ### Returns:
        - `Union[int, float]` number of this method's units.
        """
        return self._round(
            self.result.seconds, self.locale._millisecond.scale, max_precision
        )

    def to_seconds(self, max_precision=2) -> typing.Union[int, float]:
        """Convert the total seconds to seconds.

        ### Args:
        - `max_precision` (`Union[int, float]`): The maximum number of decimal places to show. The rest are
            dropped during rounding. Defaults to `2`.

        ### Returns:
        - `Union[int, float]` number of this method's units.
        """
        return self._round(
            self.result.seconds, self.locale._second.scale, max_precision
        )

    def to_minutes(self, max_precision=2) -> typing.Union[int, float]:
        """Convert the total seconds to minutes.

        ### Args:
        - `max_precision` (`Union[int, float]`): The maximum number of decimal places to show. The rest are
            dropped during rounding. Defaults to `2`.

        ### Returns:
        - `Union[int, float]` number of this method's units.
        """
        return self._round(
            self.result.seconds, self.locale._minute.scale, max_precision
        )

    def to_hours(self, max_precision=2) -> typing.Union[int, float]:
        """Convert the total seconds to hours.

        ### Args:
        - `max_precision` (`Union[int, float]`): The maximum number of decimal places to show. The rest are
            dropped during rounding. Defaults to `2`.

        ### Returns:
        - `Union[int, float]` number of this method's units.
        """
        return self._round(self.result.seconds, self.locale._hour.scale, max_precision)

    def to_days(self, max_precision=2) -> typing.Union[int, float]:
        """Convert the total seconds to days.

        ### Args:
        - `max_precision` (`Union[int, float]`): The maximum number of decimal places to show. The rest are
            dropped during rounding. Defaults to `2`.

        ### Returns:
        - `Union[int, float]` number of this method's units.
        """
        return self._round(self.result.seconds, self.locale._day.scale, max_precision)

    def to_weeks(self, max_precision=2) -> typing.Union[int, float]:
        """Convert the total seconds to weeks.

        ### Args:
        - `max_precision` (`Union[int, float]`): The maximum number of decimal places to show. The rest are
            dropped during rounding. Defaults to `2`.

        ### Returns:
        - `Union[int, float]` number of this method's units.
        """
        return self._round(self.result.seconds, self.locale._week.scale, max_precision)

    def to_months(self, max_precision=2) -> typing.Union[int, float]:
        """Convert the total seconds to months.

        ### Args:
        - `max_precision` (`Union[int, float]`): The maximum number of decimal places to show. The rest are
            dropped during rounding. Defaults to `2`.

        ### Returns:
        - `Union[int, float]` number of this method's units.
        """
        return self._round(self.result.seconds, self.locale._month.scale, max_precision)

    def to_years(self, max_precision=2) -> typing.Union[int, float]:
        """Convert the total seconds to years.

        ### Args:
        - `max_precision` (`Union[int, float]`): The maximum number of decimal places to show. The rest are
            dropped during rounding. Defaults to `2`.

        ### Returns:
        - `Union[int, float]` number of this method's units.
        """
        return self._round(self.result.seconds, self.locale._year.scale, max_precision)

    def to_decades(self, max_precision=2) -> typing.Union[int, float]:
        """Convert the total seconds to decades.

        ### Args:
        - `max_precision` (`Union[int, float]`): The maximum number of decimal places to show. The rest are
            dropped during rounding. Defaults to `2`.

        ### Returns:
        - `Union[int, float]` number of this method's units.
        """
        return self._round(
            self.result.seconds, self.locale._decade.scale, max_precision
        )

    def to_centuries(self, max_precision=2) -> typing.Union[int, float]:
        """Convert the total seconds to centuries.

        ### Args:
        - `max_precision` (`Union[int, float]`): The maximum number of decimal places to show. The rest are
        dropped during rounding. Defaults to `2`.

        ### Returns:
        - `Union[int, float]` number of this method's units.
        """
        return self._round(
            self.result.seconds, self.locale._century.scale, max_precision
        )

    def _round(
        self, total_seconds: float, scale: float, max_precision: int
    ) -> typing.Union[int, float]:
        """Round the conversion methods while checking for disabled `Scale`s."""
        try:
            return round(total_seconds / scale, max_precision)
        except ZeroDivisionError as e:
            raise DisabledScale(
                "That Scale has been disabled by being removed from the config."
            ) from e
