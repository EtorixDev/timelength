from __future__ import annotations

from datetime import datetime, timedelta, timezone

from timelength.dataclasses import ParsedTimeLength, ParserSettings
from timelength.enums import FailureFlags
from timelength.errors import DisabledScale, LocaleConfigError
from timelength.locales import LOCALES, English, Guess, Locale


class TimeLength:
    """
    Represents a length of time provided in a human readable format.

    ### Attributes

    - `content` (`str`): The string content representing the length of time.
    - `locale` (`Locale`): The locale context used for parsing the timelength string. Defaults to
        `English`. Can be set to `Guess` to guess the locale by attempting each and returning the best result.
        If `Guess`, then `locale` will be set to the guessed locale after guessing the best. Subsequent guesses
        can be made by setting `guess_locale` to `True` when calling the `parse` method. Any `FailureFlags` or
        `ParserSettings` passed to `Guess` will be applied to each attempted locale.
    - `result` (`ParsedTimeLength`): The result of the parsing.
    - `delta` (`timedelta`): The total length of time parsed as a `timedelta`.

    ### Methods

    - `parse`: Parse the `content` attribute based on `locale`, `locale.flags` and `locale.settings`. Automatically called
        during initialization. Manually call this method again if changes are made to `content` or `locale`. Guess the
        locale by passing `True` for `guess_locale`.
    - `ago`: Return a `datetime` from the past based on the parsed timelength.
    - `hence`: Return a `datetime` from the future based on the parsed timelength.
    - `to_milliseconds`, `to_seconds`, `to_minutes`, `to_hours`, `to_days`, `to_weeks`, `to_months`,
        `to_years`, `to_decades`, `to_centuries`: Convert the total duration to the respective
        units of each method with specified precision.
    - `__str__`: Return the `delta` as a string.
    - `__repr__`: Return a string representation of the `TimeLength` with attributes included.
    - `__add__`, `__radd__`, `__sub__`, `__rsub__`: Perform absolute arithmetic operations between `TimeLength`s, numbers,
        `datetime`s, and `timedelta`s. Returns a `TimeLength` or a `datetime`. The settings of the first `TimeLength` object
        will be used for the parsing of the subsequent `TimeLength`.
    - `__mul__`, `__rmul__`, `__truediv__`, `__floordiv__`: Perform absolute arithmetic operations between a `TimeLength`
        and a number. Returns a `TimeLength`.
    - `__gt__`, `__ge__`, `__lt__`, `__le__`, `__eq__`, `__ne__`: Compare two `TimeLength`s by their parsed seconds. Returns
        a bool.
    - `__bool__`: Returns if the `TimeLength` parsing succeeded based on the `result.success` attribute.
    - `__len__`: Returns the length of the `content` attribute.

    ### Raises
    - `DisabledScale`: Raised when a conversion method for a disabled `Scale` is called.
    - `LocaleConfigError`: Raised when the `Locale` doesn't have a valid parser function attached.
    - `NotImplementedError`: Raised when performing arithmetic or comparison operations with unsupported types.

    ### Example

    ```python
    time_length = TimeLength("2 hours 30 minutes")
    if time_length.result.success:
        print(f"Total Seconds: {time_length.to_seconds()}")
    ```
    """

    def __init__(self, content: str | float | int = "", locale: Locale = English()) -> None:
        """Initialize the `TimeLength` based on passed settings and call the `parse` method."""
        self.content: str = str(content) if not isinstance(content, str) else content
        self.locale: Locale = locale() if isinstance(locale, type) else locale
        self.result: ParsedTimeLength = ParsedTimeLength()
        self.delta: timedelta = timedelta()
        self.parse(guess_locale=isinstance(locale, Guess))

    def __str__(self) -> str:
        """Return the timedelta as a string."""
        return f"TimeLength: {self.delta}"

    def __repr__(self) -> str:
        """Return a string representation of the `TimeLength` with attributes included."""
        return f'TimeLength(content="{self.content}", locale={repr(self.locale)})'

    def __add__(self, other: "TimeLength | datetime | timedelta | float | int") -> "TimeLength | datetime":
        """Return an increased `TimeLength` or future `datetime` based on the added object."""
        if isinstance(other, datetime):
            return self.hence(other)
        elif isinstance(other, timedelta):
            return TimeLength(
                content=f"{abs((self.delta + other).total_seconds())} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
                locale=self.locale,
            )
        elif isinstance(other, (TimeLength, float, int)):
            return TimeLength(
                content=f"{abs(self.result.seconds + (other.result.seconds if isinstance(other, TimeLength) else other))} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
                locale=self.locale,
            )
        else:
            raise NotImplementedError("Addition with TimeLength and unsupported type.")

    def __radd__(self, other: "TimeLength | datetime | timedelta | float | int") -> "TimeLength | datetime":
        """Return an increased `TimeLength` or future `datetime` based on the added object."""
        return self.__add__(other)

    def __sub__(self, other: "TimeLength | datetime | timedelta | float | int") -> "TimeLength | datetime":
        """
        Return the difference between two `TimeLength`s, between a `TimeLength` and a number, or a past `datetime` based on
        the subtracted object.
        """
        if isinstance(other, datetime):
            return self.ago(other)
        elif isinstance(other, timedelta):
            return TimeLength(
                content=f"{abs((self.delta + other).total_seconds())} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
                locale=self.locale,
            )
        elif isinstance(other, (TimeLength, float, int)):
            return TimeLength(
                content=f"{abs(self.result.seconds - (other.result.seconds if isinstance(other, TimeLength) else other))} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
                locale=self.locale,
            )
        else:
            raise NotImplementedError("Subtraction with TimeLength and unsupported type.")

    def __rsub__(self, other: "TimeLength | datetime | timedelta | float | int") -> "TimeLength | datetime":
        """
        Return the difference between two `TimeLength`s, between a `TimeLength` and a number, or a past `datetime` based on
        the subtracted object.
        """
        return self.__sub__(other)

    def __mul__(self, other: float | int) -> "TimeLength":
        """Return a `TimeLength` multiplied by a number."""
        if not isinstance(other, (float, int)):
            raise NotImplementedError("Multiplication with TimeLength and unsupported type.")

        return TimeLength(
            content=f"{abs(self.result.seconds * other)} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
            locale=self.locale,
        )

    def __rmul__(self, other: float | int) -> "TimeLength":
        """Return a `TimeLength` multiplied by a number."""
        return self.__mul__(other)

    def __truediv__(self, other: float | int) -> "TimeLength":
        """Return a `TimeLength` divided by a number."""
        if not isinstance(other, (float, int)):
            raise NotImplementedError("Division with TimeLength and unsupported type.")

        return TimeLength(
            content=f"{abs(self.result.seconds / other)} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
            locale=self.locale,
        )

    def __rtruediv__(self, _) -> None:
        """Dividing by a TimeLength and unsupported type."""
        raise NotImplementedError("Dividing by a TimeLength and unsupported type.")

    def __floordiv__(self, other: float | int) -> "TimeLength":
        """Return a `TimeLength` floor divided by a number."""
        if not isinstance(other, (float, int)):
            raise NotImplementedError("Floor division with TimeLength and unsupported type.")

        return TimeLength(
            content=f"{abs(self.result.seconds // other)} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
            locale=self.locale,
        )

    def __rfloordiv__(self, _) -> None:
        """Dividing by a TimeLength and unsupported type."""
        raise NotImplementedError("Dividing by a TimeLength and unsupported type.")

    def __gt__(self, other: "TimeLength") -> bool:
        """Return if the `TimeLength` is greater than another `TimeLength`."""
        if not isinstance(other, TimeLength):
            raise NotImplementedError("Comparison with TimeLength and unsupported type.")
        return self.result.seconds > other.result.seconds

    def __ge__(self, other: "TimeLength") -> bool:
        """Return if the `TimeLength` is greater than or equal to another `TimeLength`."""
        if not isinstance(other, TimeLength):
            raise NotImplementedError("Comparison with TimeLength and unsupported type.")
        return self.result.seconds >= other.result.seconds

    def __lt__(self, other: "TimeLength") -> bool:
        """Return if the `TimeLength` is less than another `TimeLength`."""
        if not isinstance(other, TimeLength):
            raise NotImplementedError("Comparison with TimeLength and unsupported type.")
        return self.result.seconds < other.result.seconds

    def __le__(self, other: "TimeLength") -> bool:
        """Return if the `TimeLength` is less than or equal to another `TimeLength`."""
        if not isinstance(other, TimeLength):
            raise NotImplementedError("Comparison with TimeLength and unsupported type.")
        return self.result.seconds <= other.result.seconds

    def __eq__(self, other: "TimeLength") -> bool:
        """Return if the `TimeLength` is equal to another `TimeLength`."""
        if not isinstance(other, TimeLength):
            raise NotImplementedError("Comparison with TimeLength and unsupported type.")
        return self.result.seconds == other.result.seconds

    def __ne__(self, other: "TimeLength") -> bool:
        """Return if the `TimeLength` is not equal to another `TimeLength`."""
        if not isinstance(other, TimeLength):
            raise NotImplementedError("Comparison with TimeLength and unsupported type.")
        return self.result.seconds != other.result.seconds

    def __bool__(self) -> bool:
        """Return if the `TimeLength` parsing succeeded."""
        return self.result.success

    def __len__(self) -> int:
        """Return the length of the `TimeLength`'s `content` attribute."""
        return len(self.content)

    def _parse_locale(self, locale: Locale) -> tuple[ParsedTimeLength, Locale]:
        """Parse the content using the parser attached to the `TimeLength`'s `Locale`."""
        if hasattr(locale, "_parser") and locale._parser and callable(locale._parser):
            result: ParsedTimeLength = ParsedTimeLength()
            locale._parser(self.content.strip(), locale, result)
            return (result, locale)
        else:
            self.locale = locale
            raise LocaleConfigError(f"Parser function not found attached to {locale}.") from None

    def parse(self, guess_locale: bool = False) -> None:
        """
        Parse the passed content using the parser attached to the `TimeLength`'s `Locale`.

        ### Args:
        - `guess_locale` (`bool`): Defaults to `False`. If `True`, then the `Locale` will be guessed by attempting
            each `Locale` attached to `timelength.LOCALES` and returning the best result. The best result is the one with
            the least invalid results.
        """
        if not guess_locale:
            self.result, self.locale = self._parse_locale(self.locale)
        else:
            flags: FailureFlags = self.locale.flags
            settings: ParserSettings = self.locale.settings
            results: list[tuple[ParsedTimeLength, Locale]] = []

            for locale in LOCALES:
                if isinstance(locale, type):
                    locale = locale(flags=flags, settings=settings)
                else:
                    locale.flags = flags
                    locale.settings = settings

                results.append(self._parse_locale(locale))

            # Sort most invalid to least invalid, breaking ties by least valid to most valid, lastly breaking further ties by
            # reverse alphabetical Locale name. Everything aforementioned is in reverse order due to a limitation on reverse
            # alphabetical sorting, so the final reverse rights it.
            results.sort(
                key=lambda res: (len(res[0].invalid), -len(res[0].valid), res[1].__class__.__name__), reverse=True
            )

            # The last element is the best result.
            self.result, self.locale = results[-1]

        self.delta = timedelta(seconds=self.result.seconds)

    def ago(self, base: datetime = datetime.now(timezone.utc)) -> datetime:
        """
        Return a datetime from the past based on the parsed timelength.

        ### Args:
        - `base` (`datetime`): The `datetime` object to subtract the `delta` attribute from. Defaults to

        ### Returns:
        - `datetime` representing the `base` minus the `self.delta` attribute.
        """
        return base - self.delta

    def hence(self, base: datetime = datetime.now(timezone.utc)) -> datetime:
        """
        Return a datetime from the future based on the parsed timelength.

        ### Args:
        - `base` (`datetime`): The `datetime` object to add the `delta` attribute to. Defaults to

        ### Returns:
        - `datetime` representing the `base` plus the `self.delta` attribute.
        """
        return base + self.delta

    def to_milliseconds(self, max_precision=2) -> float:
        """
        Convert the total seconds to milliseconds.

        ### Args:
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are
        dropped during rounding. Defaults to `2`.

        ### Returns:
        - `float` number of this method's units.
        """
        return self._round(self.result.seconds, self.locale._millisecond.scale, max_precision)

    def to_seconds(self, max_precision=2) -> float:
        """
        Convert the total seconds to seconds.

        ### Args:
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are
            dropped during rounding. Defaults to `2`.

        ### Returns:
        - `float` number of this method's units.
        """
        return self._round(self.result.seconds, self.locale._second.scale, max_precision)

    def to_minutes(self, max_precision=2) -> float:
        """
        Convert the total seconds to minutes.

        ### Args:
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are
            dropped during rounding. Defaults to `2`.

        ### Returns:
        - `float` number of this method's units.
        """
        return self._round(self.result.seconds, self.locale._minute.scale, max_precision)

    def to_hours(self, max_precision=2) -> float:
        """
        Convert the total seconds to hours.

        ### Args:
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are
            dropped during rounding. Defaults to `2`.

        ### Returns:
        - `float` number of this method's units.
        """
        return self._round(self.result.seconds, self.locale._hour.scale, max_precision)

    def to_days(self, max_precision=2) -> float:
        """
        Convert the total seconds to days.

        ### Args:
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are
            dropped during rounding. Defaults to `2`.

        ### Returns:
        - `float` number of this method's units.
        """
        return self._round(self.result.seconds, self.locale._day.scale, max_precision)

    def to_weeks(self, max_precision=2) -> float:
        """
        Convert the total seconds to weeks.

        ### Args:
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are
            dropped during rounding. Defaults to `2`.

        ### Returns:
        - `float` number of this method's units.
        """
        return self._round(self.result.seconds, self.locale._week.scale, max_precision)

    def to_months(self, max_precision=2) -> float:
        """
        Convert the total seconds to months.

        ### Args:
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are
            dropped during rounding. Defaults to `2`.

        ### Returns:
        - `float` number of this method's units.
        """
        return self._round(self.result.seconds, self.locale._month.scale, max_precision)

    def to_years(self, max_precision=2) -> float:
        """
        Convert the total seconds to years.

        ### Args:
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are
            dropped during rounding. Defaults to `2`.

        ### Returns:
        - `float` number of this method's units.
        """
        return self._round(self.result.seconds, self.locale._year.scale, max_precision)

    def to_decades(self, max_precision=2) -> float:
        """
        Convert the total seconds to decades.

        ### Args:
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are
            dropped during rounding. Defaults to `2`.

        ### Returns:
        - `float` number of this method's units.
        """
        return self._round(self.result.seconds, self.locale._decade.scale, max_precision)

    def to_centuries(self, max_precision=2) -> float:
        """
        Convert the total seconds to centuries.

        ### Args:
        - `max_precision` (`int`): The maximum number of decimal places to show. The rest are
        dropped during rounding. Defaults to `2`.

        ### Returns:
        - `float` number of this method's units.
        """
        return self._round(self.result.seconds, self.locale._century.scale, max_precision)

    def _round(self, total_seconds: float, scale: float, max_precision: int) -> float:
        """Round the conversion methods while checking for disabled `Scale`s."""
        try:
            return float(round(total_seconds / scale, max_precision))
        except ZeroDivisionError as e:
            raise DisabledScale("That Scale has been disabled by being removed from the config.") from e
