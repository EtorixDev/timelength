from __future__ import annotations

from datetime import datetime, timedelta, timezone

from timelength.dataclasses import ParsedTimeLength, ParserSettings, Scale
from timelength.enums import FailureFlags
from timelength.errors import DisabledScale, LocaleConfigError
from timelength.locales import LOCALES, English, Guess, Locale


class TimeLength:
    """
    Represents a length of time.

    #### Arguments
    - content: `str` — The length of time to be parsed.
    - locale: `Locale = English()` — The locale context used for parsing the content.
        - Can be set to `Guess()` to attempt each locale attached to `LOCALES`, keeping the best result.
        - Include custom locales in the pool by appending them to `LOCALES`.
        - The best result is the one with the least invalid results.
        - The chosen locale will overwrite `locale`.

    #### Attributes
    - result: `ParsedTimeLength` — An object containing the parsed content.
    - delta: `timedelta` — The total length of time parsed as a `timedelta`.
        - If the parsing failed this attribute will be an empty `timedelta()`.
        - If the parsed value exceeds the maximum supported by `timedelta`, this attribute will be `timedelta.max` and
            the `ago()` and `hence()` methods will raise an `OverflowError` if used.

    #### Methods
    - `parse()` — Parse the `content` based on the `locale`.
        - Automatically called during initialization. Manually call this method again if changes are made to `content`
            or `locale`.
    - `ago()` — Return a `datetime` from the past adjusted for the parsed timelength.
    - `hence()` — Return a `datetime` from the future adjusted for the parsed timelength.
    - `to_milliseconds()`, `to_seconds()`, `to_minutes()`, `to_hours()`, `to_days()`, `to_weeks()`, `to_months()`,
        `to_years()`, `to_decades()`, `to_centuries()`
      - Convert the parsed duration to the respective units of each method.

    #### Raises
    - `DisabledScale` — Raised when a conversion method for a disabled `Scale` is called.
    - `LocaleConfigError` — Raised when `locale` doesn't have a valid parser function attached.
    - `NotImplementedError` — Raised when performing arithmetic or comparison operations with unsupported types.

    #### Example
    ```python
    from timelength import TimeLength

    tl = TimeLength("2 hours 30 minutes")
    print(f"Total Seconds: {tl.to_seconds()}")
    ```
    """

    def __init__(self, content: str, locale: Locale = English()) -> None:
        self.content: str = content
        self.locale: Locale = locale() if isinstance(locale, type) else locale
        self.result: ParsedTimeLength = None
        self.delta: timedelta = None
        self.parse(guess_locale=isinstance(locale, Guess))

    def _parse_locale(self, locale: Locale) -> tuple[ParsedTimeLength, Locale]:
        if hasattr(locale, "_parser") and callable(locale._parser):
            result: ParsedTimeLength = ParsedTimeLength()
            locale._parser(self.content.strip(), locale, result)
            return (result, locale)
        else:
            self.locale = locale
            self.result = ParsedTimeLength()
            self.delta = timedelta()
            if isinstance(locale, Locale):
                raise LocaleConfigError(f"Parser function not found attached to {locale}.") from None
            else:
                raise LocaleConfigError("Invalid value provided for locale.") from None

    def parse(self, guess_locale: bool = False) -> None:
        """
        Parse `self.content` using the parser attached to `self.locale`. Updates `self.result` and `self.delta`.

        #### Arguments
        - guess_locale: `bool = False` — Attempt each `Locale` attached to `LOCALES` and keep the best result.
            - The best result is the one with the least invalid results.
            - The chosen locale will overwrite `self.locale`.
            - Include custom locales in the pool by appending them to `LOCALES`.
        """

        if not guess_locale:
            self.result, self.locale = self._parse_locale(self.locale)
        else:
            # Flags and settings passed to Guess to overwrite config values.
            # If None, the config values of each locale will be used.
            flags: FailureFlags = self.locale.flags
            settings: ParserSettings = self.locale.settings
            results: list[tuple[ParsedTimeLength, Locale]] = []

            for locale in LOCALES:
                if isinstance(locale, type):
                    locale = locale(flags=flags, settings=settings)
                else:
                    locale.flags = flags if flags else locale.flags
                    locale.settings = settings if settings else locale.settings

                results.append(self._parse_locale(locale))

            # Sort most invalid to least invalid, breaking ties by least valid to most valid, lastly breaking further
            # ties by reverse alphabetical Locale name. Everything aforementioned is written opposite due to a
            # limitation on reverse alphabetical sorting, so the final reverse rights it.
            results.sort(
                key=lambda res: (len(res[0].invalid), -len(res[0].valid), res[1].__class__.__name__), reverse=True
            )

            self.result, self.locale = results[-1]

        try:
            self.delta = timedelta(seconds=self.result.seconds)
        except OverflowError:
            self.delta = timedelta.max

    def ago(self, base: datetime = datetime.now(timezone.utc)) -> datetime:
        """
        Return a datetime from the past based on the parsed timelength.

        #### Arguments
        - base: `datetime = datetime.now(timezone.utc)` — The relative time to subtract the `delta` attribute from.

        #### Raises
        - `OverflowError` — Raised when the parsed value exceeds the supported bounds of `timedelta`.
        - `OverflowError` — Raised when the resultant datetime would exceed the supported bounds of `datetime`.

        #### Returns
        - A `datetime` representing `base` minus `self.delta`.
        """

        if self.delta == timedelta.max:
            raise OverflowError("The parsed value exceeds the supported bounds of timedelta.")
        elif self._invalid_datetime(base, -self.delta):
            raise OverflowError("The resultant datetime would exceed the supported bounds of datetime.")
        else:
            return base - self.delta

    def hence(self, base: datetime = datetime.now(timezone.utc)) -> datetime:
        """
        Return a datetime from the future based on the parsed timelength.

        #### Arguments
        - base: `datetime = datetime.now(timezone.utc)`: The relative time to subtract the `delta` attribute from.

        #### Raises
        - `OverflowError` — Raised when the parsed value exceeds the supported bounds of `timedelta`.
        - `OverflowError` — Raised when the resultant datetime would exceed the supported bounds of `datetime`.

        #### Returns
        - A `datetime` representing `base` plus `self.delta`.
        """

        if self.delta == timedelta.max:
            raise OverflowError("The parsed value exceeds the supported bounds of timedelta.")
        elif self._invalid_datetime(base, self.delta):
            raise OverflowError("The resultant datetime would exceed the supported bounds of datetime.")
        else:
            return base + self.delta

    def to_milliseconds(self, max_precision=2) -> float:
        """
        Convert the parsed seconds to milliseconds.

        #### Arguments
        - max_precision: `int = 2` — The maximum number of decimal places to include.

        #### Raises
        - `DisabledScale` — Raised when `Millisecond` is disabled.

        #### Returns
        - A `float` of this method's units.
        """

        return self._round(self.result.seconds, self.locale._millisecond, max_precision)

    def to_seconds(self, max_precision=2) -> float:
        """
        Convert the parsed seconds to seconds.

        #### Arguments
        - max_precision: `int = 2` — The maximum number of decimal places to include.

        #### Raises
        - `DisabledScale` — Raised when `Second` is disabled.

        #### Returns
        - A `float` of this method's units.
        """

        return self._round(self.result.seconds, self.locale._second, max_precision)

    def to_minutes(self, max_precision=2) -> float:
        """
        Convert the parsed seconds to minutes.

        #### Arguments
        - max_precision: `int = 2` — The maximum number of decimal places to include.

        #### Raises
        - `DisabledScale` — Raised when `Minute` is disabled.

        #### Returns
        - A `float` of this method's units.
        """

        return self._round(self.result.seconds, self.locale._minute, max_precision)

    def to_hours(self, max_precision=2) -> float:
        """
        Convert the parsed seconds to hours.

        #### Arguments
        - max_precision: `int = 2` — The maximum number of decimal places to include.

        #### Raises
        - `DisabledScale` — Raised when `Hour` is disabled.

        #### Returns
        - A `float` of this method's units.
        """

        return self._round(self.result.seconds, self.locale._hour, max_precision)

    def to_days(self, max_precision=2) -> float:
        """
        Convert the parsed seconds to days.

        #### Arguments
        - max_precision: `int = 2` — The maximum number of decimal places to include.

        #### Raises
        - `DisabledScale` — Raised when `Day` is disabled.

        #### Returns
        - A `float` of this method's units.
        """

        return self._round(self.result.seconds, self.locale._day, max_precision)

    def to_weeks(self, max_precision=2) -> float:
        """
        Convert the parsed seconds to weeks.

        #### Arguments
        - max_precision: `int = 2` — The maximum number of decimal places to include.

        #### Raises
        - `DisabledScale` — Raised when `Week` is disabled.

        #### Returns
        - A `float` of this method's units.
        """

        return self._round(self.result.seconds, self.locale._week, max_precision)

    def to_months(self, max_precision=2) -> float:
        """
        Convert the parsed seconds to months.

        #### Arguments
        - max_precision: `int = 2` — The maximum number of decimal places to include.

        #### Raises
        - `DisabledScale` — Raised when `Month` is disabled.

        #### Returns
        - A `float` of this method's units.
        """

        return self._round(self.result.seconds, self.locale._month, max_precision)

    def to_years(self, max_precision=2) -> float:
        """
        Convert the parsed seconds to years.

        #### Arguments
        - max_precision: `int = 2` — The maximum number of decimal places to include.

        #### Raises
        - `DisabledScale` — Raised when `Year` is disabled.

        #### Returns
        - A `float` of this method's units.
        """

        return self._round(self.result.seconds, self.locale._year, max_precision)

    def to_decades(self, max_precision=2) -> float:
        """
        Convert the parsed seconds to decades.

        #### Arguments
        - max_precision: `int = 2` — The maximum number of decimal places to include.

        #### Raises
        - `DisabledScale` — Raised when `Decade` is disabled.

        #### Returns
        - A `float` of this method's units.
        """

        return self._round(self.result.seconds, self.locale._decade, max_precision)

    def to_centuries(self, max_precision=2) -> float:
        """
        Convert the parsed seconds to centuries.

        #### Arguments
        - max_precision: `int = 2` — The maximum number of decimal places to include.

        #### Raises
        - `DisabledScale` — Raised when `Century` is disabled.

        #### Returns
        - A `float` of this method's units.
        """

        return self._round(self.result.seconds, self.locale._century, max_precision)

    def _round(self, total_seconds: float, scale: Scale, max_precision: int) -> float:
        if scale.scale:
            return float(round(total_seconds / scale.scale, max_precision))
        else:
            raise DisabledScale(
                f"{scale.plural.capitalize()} has been disabled by having its value set to 0."
                if scale.plural
                else "That scale has been disabled by being removed from the config."
            )

    def __str__(self) -> str:
        """Return a formatted string with `self.delta`."""
        return f"TimeLength: {self.delta}"

    def __repr__(self) -> str:
        """Return a string representation of `self` with attributes included."""
        return f'TimeLength(content="{self.content}", locale={repr(self.locale)})'

    def _invalid_datetime(self, date: datetime, delta: timedelta) -> bool:
        """Check if the resultant datetime would exceed the supported bounds of datetime."""
        return (date_sec := date.timestamp()) + (
            delta_sec := delta.total_seconds()
        ) < datetime.min.timestamp() or date_sec + delta_sec > datetime.max.timestamp()

    def _invalid_timedelta(self, first: timedelta, second: timedelta) -> bool:
        """Check if the resultant timedelta would exceed the supported bounds of timedelta."""
        return (first_sec := first.total_seconds()) + (
            second_sec := second.total_seconds()
        ) < timedelta.min.total_seconds() or first_sec + second_sec > timedelta.max.total_seconds()

    def __add__(self, other: "TimeLength | timedelta | float | int") -> "TimeLength":
        """
        Get the sum of `self` and a `TimeLength`, a `timedelta`, or a number. Returned `TimeLength`s are absolute.

        #### Arguments
        - other: `TimeLength | timedelta | float | int` — The object to add to `self`.

        #### Returns
        - A `TimeLength` that represents the absolute sum of `self` and the passed value.
        """

        if isinstance(other, TimeLength):
            return TimeLength(
                content=f"{abs(self.result.seconds + other.result.seconds)} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
                locale=self.locale,
            )
        elif isinstance(other, timedelta):
            return TimeLength(
                content=f"{abs(self.result.seconds + other.total_seconds())} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
                locale=self.locale,
            )
        elif isinstance(other, (float, int)):
            return TimeLength(
                content=f"{abs(self.result.seconds + other)} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
                locale=self.locale,
            )
        else:
            return NotImplemented

    def __radd__(self, other: "TimeLength | datetime | timedelta") -> "TimeLength | datetime | timedelta":
        """
        Get the sum of a `TimeLength`, a `datetime`, or a `timedelta` and `self`. Returned `TimeLength`s are absolute.

        #### Arguments
        - other: `TimeLength | datetime | timedelta` — The object to add `self` to.

        #### Raises
        - `OverflowError` — Raised when the parsed value exceeds the supported bounds of `timedelta`.
        - `OverflowError` — Raised when the resultant datetime would exceed the supported bounds of `datetime`.
        - `OverflowError` — Raised when the resultant timedelta would exceed the supported bounds of `timedelta`.

        #### Returns
        - A `TimeLength` that represents the absolute sum of the passed value and `self`.
        - A `datetime` in the future by the amount of `self.delta`.
        - A `timedelta` that represents the sum of the passed value and `self.delta`.
        """

        if isinstance(other, TimeLength):
            return TimeLength(
                content=f"{abs(self.result.seconds + other.result.seconds)} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
                locale=self.locale,
            )
        elif isinstance(other, datetime):
            return self.hence(other)
        elif isinstance(other, timedelta):
            if self.delta == timedelta.max:
                raise OverflowError("The parsed value exceeds the supported bounds of timedelta.")
            elif self._invalid_timedelta(other, self.delta):
                raise OverflowError("The resultant timedelta would exceed the supported bounds of timedelta.")

            return self.delta + other
        else:
            return NotImplemented

    def __sub__(self, other: "TimeLength | timedelta | float | int") -> "TimeLength":
        """
        Get the difference between `self` and a `TimeLength`, a `timedelta`, or a number. Returned `TimeLength`s are
        absolute.

        #### Arguments
        - other: `TimeLength | timedelta | float | int` — The object to subtract from `self`.

        #### Returns
        - A `TimeLength` that represents the absolute difference between `self` and the passed value.
        """

        if isinstance(other, TimeLength):
            return TimeLength(
                content=f"{abs(self.result.seconds - other.result.seconds)} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
                locale=self.locale,
            )
        elif isinstance(other, timedelta):
            return TimeLength(
                content=f"{abs(self.result.seconds - other.total_seconds())} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
                locale=self.locale,
            )
        elif isinstance(other, (float, int)):
            return TimeLength(
                content=f"{abs(self.result.seconds - other)} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
                locale=self.locale,
            )
        else:
            return NotImplemented

    def __rsub__(self, other: "TimeLength | datetime | timedelta") -> "TimeLength | datetime | timedelta":
        """
        Get the difference between a `TimeLength`, a `datetime`, or a `timedelta` and `self`. Returned `TimeLength`s
        are absolute.

        #### Arguments
        - other: `TimeLength | datetime | timedelta` — The object to subtract `self` from.

        #### Raises
        - `OverflowError` — Raised when the parsed value exceeds the supported bounds of `timedelta`.
        - `OverflowError` — Raised when the resultant datetime would exceed the supported bounds of `datetime`.
        - `OverflowError` — Raised when the resultant timedelta would exceed the supported bounds of `timedelta`.

        #### Returns
        - A `TimeLength` that represents the absolute difference between the passed value and `self`.
        - A `datetime` in the past by the amount of `self.delta`.
        - A `timedelta` that represents the difference between the passed value and `self.delta`.
        """

        if isinstance(other, TimeLength):
            return TimeLength(
                content=f"{abs(other.result.seconds - self.result.seconds)} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
                locale=self.locale,
            )
        elif isinstance(other, datetime):
            return self.ago(other)
        elif isinstance(other, timedelta):
            if self.delta == timedelta.max:
                raise OverflowError("The parsed value exceeds the supported bounds of timedelta.")
            elif self._invalid_timedelta(other, -self.delta):
                raise OverflowError("The resultant timedelta would exceed the supported bounds of timedelta.")

            return other - self.delta
        else:
            return NotImplemented

    def __mul__(self, other: float | int) -> "TimeLength":
        """
        Get the absolute multiplication of `self` and a number.

        #### Arguments
        - other: `float | int` — The number to multiply `self` by.

        #### Returns
        - A `TimeLength` that represents the absolute multiplication of `self` and the passed number.
        """

        if not isinstance(other, (float, int)):
            return NotImplemented

        return TimeLength(
            content=f"{abs(self.result.seconds * other)} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
            locale=self.locale,
        )

    __rmul__ = __mul__

    def __truediv__(self, other: "TimeLength | timedelta | float | int") -> "TimeLength | float":
        """
        Get the division of `self` and a `TimeLength`, a `timedelta`, or a number. Returned `TimeLength`s are absolute.

        #### Arguments
        - other: `TimeLength | timedelta | float | int` — The object to divide `self` by.

        #### Returns
        - A `TimeLength` that represents the absolute division of `self` and the passed number.
        - A `float` that represents the division of `self` and the passed `TimeLength` or `timedelta`.
        """

        if isinstance(other, TimeLength):
            return self.result.seconds / other.result.seconds
        elif isinstance(other, timedelta):
            return self.result.seconds / other.total_seconds()
        elif isinstance(other, (float, int)):
            return TimeLength(
                content=f"{abs(self.result.seconds / other)} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
                locale=self.locale,
            )
        else:
            return NotImplemented

    def __rtruediv__(self, other: "TimeLength | timedelta") -> float:
        """
        Get the division of a `TimeLength` or `timedelta` and `self`.

        #### Arguments
        - other: `TimeLength | timedelta` — The object to divide with `self`.

        #### Returns
        - A `float` that represents the division of the passed `TimeLength` or `timedelta` and `self`.
        """

        if isinstance(other, TimeLength):
            return other.result.seconds / self.result.seconds
        elif isinstance(other, timedelta):
            return other.total_seconds() / self.result.seconds
        else:
            return NotImplemented

    def __floordiv__(self, other: "TimeLength | timedelta | float | int") -> "TimeLength | float":
        """
        Get the floor division of `self` and a `TimeLength`, a `timedelta`, or a number. Returned `TimeLength`s are
        absolute.

        #### Arguments
        - other: `TimeLength | timedelta | float | int` — The object to divide `self` by.

        #### Returns
        - A `TimeLength` that represents the absolute floor division of `self` and the passed number.
        - A `float` that represents the floor division of `self` and the passed `TimeLength` or `timedelta`.
        """

        if isinstance(other, TimeLength):
            return self.result.seconds // other.result.seconds
        elif isinstance(other, timedelta):
            return self.result.seconds // other.total_seconds()
        elif isinstance(other, (float, int)):
            return TimeLength(
                content=f"{abs(self.result.seconds // other)} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
                locale=self.locale,
            )
        else:
            return NotImplemented

    def __rfloordiv__(self, other: "TimeLength | timedelta") -> float:
        """
        Get the floor division of a `TimeLength` or `timedelta` and `self`.

        #### Arguments
        - other: `TimeLength | timedelta` — The object to divide with `self`.

        #### Returns
        - A `float` that represents the floor division of the passed `TimeLength` or `timedelta` and `self`.
        """

        if isinstance(other, TimeLength):
            return other.result.seconds // self.result.seconds
        elif isinstance(other, timedelta):
            return other.total_seconds() // self.result.seconds
        else:
            return NotImplemented

    def __mod__(self, other: "TimeLength | timedelta") -> "TimeLength":
        """
        Get the modulo of `self` and a `TimeLength` or `timedelta`.

        #### Arguments
        - other: `TimeLength | timedelta` — The object to modulo `self` by.

        #### Returns
        - A `TimeLength` that represents the absolute modulo of `self` and the passed `TimeLength` or `timedelta`.
        """

        if isinstance(other, TimeLength):
            return TimeLength(
                content=f"{abs(self.result.seconds % other.result.seconds)} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
                locale=self.locale,
            )
        elif isinstance(other, timedelta):
            return TimeLength(
                content=f"{abs(self.result.seconds % other.total_seconds())} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
                locale=self.locale,
            )
        else:
            return NotImplemented

    def __rmod__(self, other: "TimeLength | timedelta") -> "TimeLength | timedelta":
        """
        Get the modulo of a `TimeLength` or `timedelta` and `self`.

        #### Arguments
        - other: `TimeLength | timedelta` — The object to modulo with `self`.

        #### Returns
        - A `TimeLength` that represents the absolute modulo of the passed `TimeLength` and `self`.
        - A `timedelta` that represents the modulo of the passed `timedelta` and `self`.
        """

        if isinstance(other, TimeLength):
            return TimeLength(
                content=f"{abs(other.result.seconds % self.result.seconds)} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
                locale=self.locale,
            )
        elif isinstance(other, timedelta):
            return other % self.delta
        else:
            return NotImplemented

    def __divmod__(self, other: "TimeLength | timedelta") -> tuple[float, "TimeLength"]:
        """
        Get the divmod of `self` and a `TimeLength` or `timedelta`.

        #### Arguments
        - other: `TimeLength | timedelta` — The object to divmod `self` by.

        #### Returns
        - A tuple of a `float` and a `TimeLength` that represent the absolute divmod of `self` and the passed
            `TimeLength` or `timedelta`.
        """

        if isinstance(other, (TimeLength, timedelta)):
            return (
                self // other,
                self % other,
            )
        else:
            return NotImplemented

    def __rdivmod__(self, other: "TimeLength | timedelta") -> tuple[float, "TimeLength | timedelta"]:
        """
        Get the divmod of a `TimeLength` or `timedelta` and `self`.

        #### Arguments
        - other: `TimeLength | timedelta` — The object to divmod with `self`.

        #### Returns
        - A tuple of a `float` and a `TimeLength` or `timedelta` that represent the absolute divmod of the passed
            `TimeLength` or `timedelta` and `self`.
        """

        if isinstance(other, (TimeLength, timedelta)):
            return (
                other // self,
                other % self,
            )
        else:
            return NotImplemented

    def __pow__(self, other: float | int, mod: "TimeLength | timedelta" = None) -> "TimeLength":
        """
        Get the absolute power of `self` and a number.

        #### Arguments
        - other: `float | int` — The number to raise `self` to.
        - mod: `TimeLength | timedelta = None` — The object to modulo the result by.

        #### Returns
        - A `TimeLength` that represents the absolute power of `self` and the passed number, optionally moduloed by `mod`.
        """

        if not isinstance(other, (float, int)):
            return NotImplemented
        elif mod is not None and not isinstance(mod, (TimeLength, timedelta)):
            return NotImplemented

        if not mod:
            result = abs(self.result.seconds**other)
        else:
            mod_seconds = mod.result.seconds if isinstance(mod, TimeLength) else mod.total_seconds()
            result = abs(pow(self.result.seconds, other, int(mod_seconds)))

        return TimeLength(
            content=f"{result} {self.locale._second.plural if self.locale._second else self.locale._scales[0].plural}",
            locale=self.locale,
        )

    def __bool__(self) -> bool:
        """Return if the parsing succeeded."""
        return self.result.success

    def __len__(self) -> int:
        """Return the length of `self.content`."""
        return len(self.content)

    def __abs__(self) -> "TimeLength":
        """Return self unchanged as `TimeLength` is an absolute measurement."""
        return self

    def __pos__(self) -> "TimeLength":
        """Return self unchanged as `TimeLength` is an absolute measurement."""
        return self

    def __neg__(self) -> None:
        return NotImplemented

    def __gt__(self, other: "TimeLength | timedelta") -> bool:
        """
        Check if `self` is greater than `other`.

        #### Arguments
        - other: `TimeLength | timedelta` — The object to compare to.

        #### Returns
        - A `bool` indicating if `self` is greater than `other`.
        """

        if not isinstance(other, (TimeLength, timedelta)):
            return NotImplemented

        return self.result.seconds > (other.result.seconds if isinstance(other, TimeLength) else other.total_seconds())

    def __ge__(self, other: "TimeLength | timedelta") -> bool:
        """
        Check if `self` is greater than or equal to `other`.

        #### Arguments
        - other: `TimeLength | timedelta` — The object to compare to.

        #### Returns
        - A `bool` indicating if `self` is greater than or equal to `other`.
        """

        if not isinstance(other, (TimeLength, timedelta)):
            return NotImplemented

        return self.result.seconds >= (other.result.seconds if isinstance(other, TimeLength) else other.total_seconds())

    def __lt__(self, other: "TimeLength | timedelta") -> bool:
        """
        Check if `self` is less than `other`.

        #### Arguments
        - other: `TimeLength | timedelta` — The object to compare to.

        #### Returns
        - A `bool` indicating if `self` is less than `other`.
        """

        if not isinstance(other, (TimeLength, timedelta)):
            return NotImplemented

        return self.result.seconds < (other.result.seconds if isinstance(other, TimeLength) else other.total_seconds())

    def __le__(self, other: "TimeLength | timedelta") -> bool:
        """
        Check if `self` is less than or equal to `other`.

        #### Arguments
        - other: `TimeLength | timedelta` — The object to compare to.

        #### Returns
        - A `bool` indicating if `self` is less than or equal to `other`.
        """

        if not isinstance(other, (TimeLength, timedelta)):
            return NotImplemented

        return self.result.seconds <= (other.result.seconds if isinstance(other, TimeLength) else other.total_seconds())

    def __eq__(self, other: "TimeLength | timedelta") -> bool:
        """
        Check if `self` is equal to `other`.

        #### Arguments
        - other: `TimeLength | timedelta` — The object to compare to.

        #### Returns
        - A `bool` indicating if `self` is equal to `other`.
        """

        if not isinstance(other, (TimeLength, timedelta)):
            return NotImplemented

        return self.result.seconds == (other.result.seconds if isinstance(other, TimeLength) else other.total_seconds())

    def __ne__(self, other: "TimeLength | timedelta") -> bool:
        """
        Check if `self` is not equal to `other`.

        #### Arguments
        - other: `TimeLength | timedelta` — The object to compare to.

        #### Returns
        - A `bool` indicating if `self` is not equal to `other`.
        """

        if not isinstance(other, (TimeLength, timedelta)):
            return NotImplemented

        return self.result.seconds != (other.result.seconds if isinstance(other, TimeLength) else other.total_seconds())
