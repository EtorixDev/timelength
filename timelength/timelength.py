from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone

from timelength.dataclasses import ParsedTimeLength, Scale
from timelength.errors import (
    InvalidScaleError,
    NotALocaleError,
    ParsedTimeDeltaError,
    PotentialDateTimeError,
    PotentialTimeDeltaError,
)
from timelength.locales import English, Guess, Locale


class TimeLength:
    """---
    Represents a length of time.

    #### Attributes
    - content: `str` — The string to be parsed.
    - locale: `Locale | Guess = English()` — The context used for parsing.
        - Will be set to the guessed locale if `Guess()` is passed.

    #### Properties
    - result: `ParsedTimeLength` — The result of parsing.

    #### Methods
    - `parse()` — Parse `self.content` based on `self.locale`.
        - Automatically called during initialization. Manually call if changes are made to `self.content` or `self.locale`.
    - `ago()` — Return a `datetime` from the past adjusted for `self.result`.
    - `hence()` — Return a `datetime` from the future adjusted for `self.result`.
    - `to_milliseconds()`, `to_minutes()`, `to_hours()`, `to_days()`, `to_weeks()`, `to_months()`,
        `to_years()`, `to_decades()`, `to_centuries()`
        - Convert the parsed duration to the respective units of each method.

    #### Raises
    - `NotALocaleError` when `locale` is not an instance of `Locale` or `Guess`.
    - `InvalidParserError` when the parser on `locale` is not callable.

    #### Example
    ```python
    from timelength import TimeLength

    tl = TimeLength("2 hours 30 minutes")
    print(f"Total Seconds: {tl.result.seconds}")
    ```
    """

    def __init__(self, content: str, locale: Locale | Guess | None = None) -> None:
        self.content: str = str(content)

        # self.locale must always be a Locale, so if Guess is passed, temporarily set it to the first
        # locale in Guess().locales to prevent a wasted initialization while the best locale is found.
        self.locale: Locale = locale.locales[0] if isinstance(locale, Guess) else (locale or English())

        if not isinstance(self.locale, Locale):
            raise NotALocaleError(locale)

        self._result: ParsedTimeLength
        self.parse(guess_locale=locale if isinstance(locale, Guess) else False)

    @property
    def result(self) -> ParsedTimeLength:
        """The result of parsing."""
        return self._result

    def _parse_locale(self, locale: Locale) -> ParsedTimeLength:
        return locale.parser(self.content.strip(), locale)

    def parse(self, guess_locale: bool | Guess = False) -> None:
        """---
        Parse `self.content` using the parser attached to `self.locale`.

        #### Arguments
        - guess_locale: `bool | Guess = False` — Attempt each `Locale` and keep the best result.
            - The best result is the one with the least invalid results.
            - Pass an existing instance of `Guess` to prevent re-initializing every locale in `Guess().locales`.

        #### Updates
        - `self.result` with the outcome of parsing.
        - `self.locale` with the best locale if `guess_locale` is set.
        """

        if guess_locale is False:
            self._result = self._parse_locale(self.locale)
        else:
            guess: Guess = guess_locale if isinstance(guess_locale, Guess) else Guess()
            results: list[tuple[ParsedTimeLength, Locale]] = []

            for locale in guess.locales:
                results.append((self._parse_locale(locale), locale))

            # Sort most invalid to least invalid, breaking ties by least valid to most valid,
            # lastly breaking further ties by reverse alphabetical Locale name.
            results.sort(
                key=lambda res: (len(res[0].invalid), -len(res[0].valid), res[1].__class__.__name__), reverse=True
            )

            self._result = results[-1][0]
            self.locale = deepcopy(results[-1][1])

    def ago(self, base: datetime = datetime.now(timezone.utc)) -> datetime:
        """---
        Get a `datetime` from the past.

        #### Arguments
        - base: `datetime = datetime.now(timezone.utc)` — The relative time to subtract from.

        #### Returns
        - A `datetime` representing `base` minus `self.result.delta`.

        #### Raises
        - `ParsedTimeDeltaError` when `self.result` exceeds the supported bounds of `timedelta`.
        - `PotentialDateTimeError` when the resultant `datetime` would exceed the supported bounds of `datetime`.
        """

        if self.result.delta is None:
            raise ParsedTimeDeltaError
        elif self._invalid_datetime(base, self.result.delta, subtract=True):
            raise PotentialDateTimeError
        else:
            return base - self.result.delta

    def hence(self, base: datetime = datetime.now(timezone.utc)) -> datetime:
        """---
        Get a `datetime` from the future.

        #### Arguments
        - base: `datetime = datetime.now(timezone.utc)` — The relative time to add to.

        #### Returns
        - A `datetime` representing `base` plus `self.result.delta`.

        #### Raises
        - `ParsedTimeDeltaError` when `self.result` exceeds the supported bounds of `timedelta`.
        - `PotentialDateTimeError` when the resultant `datetime` would exceed the supported bounds of `datetime`.
        """

        if self.result.delta is None:
            raise ParsedTimeDeltaError
        elif self._invalid_datetime(base, self.result.delta):
            raise PotentialDateTimeError
        else:
            return base + self.result.delta

    def to_milliseconds(self, max_precision: int | None = None) -> float:
        """---
        Return `self.result.seconds` converted to milliseconds.

        #### Arguments
        - max_precision: `int | None = None` — The maximum number of decimal places to include.

        #### Returns
        - A `float` representing `self.result.seconds` as milliseconds.

        #### Raises
        - `InvalidScaleError` when `self.locale.millisecond` is invalid.
        """

        return self._round(self.locale.millisecond, max_precision)

    def to_minutes(self, max_precision: int | None = None) -> float:
        """---
        Return `self.result.seconds` converted to minutes.

        #### Arguments
        - max_precision: `int | None = None` — The maximum number of decimal places to include.

        #### Returns
        - A `float` representing `self.result.seconds` as minutes.

        #### Raises
        - `InvalidScaleError` when `self.locale.minute` is invalid.
        """

        return self._round(self.locale.minute, max_precision)

    def to_hours(self, max_precision: int | None = None) -> float:
        """---
        Return `self.result.seconds` converted to hours.

        #### Arguments
        - max_precision: `int | None = None` — The maximum number of decimal places to include.

        #### Returns
        - A `float` representing `self.result.seconds` as hours.

        #### Raises
        - `InvalidScaleError` when `self.locale.hour` is invalid.
        """

        return self._round(self.locale.hour, max_precision)

    def to_days(self, max_precision: int | None = None) -> float:
        """---
        Return `self.result.seconds` converted to days.

        #### Arguments
        - max_precision: `int | None = None` — The maximum number of decimal places to include.

        #### Returns
        - A `float` representing `self.result.seconds` as days.

        #### Raises
        - `InvalidScaleError` when `self.locale.day` is invalid.
        """

        return self._round(self.locale.day, max_precision)

    def to_weeks(self, max_precision: int | None = None) -> float:
        """---
        Return `self.result.seconds` converted to weeks.

        #### Arguments
        - max_precision: `int | None = None` — The maximum number of decimal places to include.

        #### Returns
        - A `float` representing `self.result.seconds` as weeks.

        #### Raises
        - `InvalidScaleError` when `self.locale.week` is invalid.
        """

        return self._round(self.locale.week, max_precision)

    def to_months(self, max_precision: int | None = None) -> float:
        """---
        Return `self.result.seconds` converted to months.

        #### Arguments
        - max_precision: `int | None = None` — The maximum number of decimal places to include.

        #### Returns
        - A `float` representing `self.result.seconds` as months.

        #### Raises
        - `InvalidScaleError` when `self.locale.month` is invalid.
        """

        return self._round(self.locale.month, max_precision)

    def to_years(self, max_precision: int | None = None) -> float:
        """---
        Return `self.result.seconds` converted to years.

        #### Arguments
        - max_precision: `int | None = None` — The maximum number of decimal places to include.

        #### Returns
        - A `float` representing `self.result.seconds` as years.

        #### Raises
        - `InvalidScaleError` when `self.locale.year` is invalid.
        """

        return self._round(self.locale.year, max_precision)

    def to_decades(self, max_precision: int | None = None) -> float:
        """---
        Return `self.result.seconds` converted to decades.

        #### Arguments
        - max_precision: `int | None = None` — The maximum number of decimal places to include.

        #### Returns
        - A `float` representing `self.result.seconds` as decades.

        #### Raises
        - `InvalidScaleError` when `self.locale.decade` is invalid.
        """

        return self._round(self.locale.decade, max_precision)

    def to_centuries(self, max_precision: int | None = None) -> float:
        """---
        Return `self.result.seconds` converted to centuries.

        #### Arguments
        - max_precision: `int | None = None` — The maximum number of decimal places to include.

        #### Returns
        - A `float` representing `self.result.seconds` as centuries.

        #### Raises
        - `InvalidScaleError` when `self.locale.century` is invalid.
        """

        return self._round(self.locale.century, max_precision)

    def _round(self, scale: Scale, max_precision: int | None) -> float:
        if not scale.valid:
            raise InvalidScaleError(scale.singular)
        else:
            val = self.result.seconds / scale.scale
            return round(val, max_precision) if max_precision else val

    def _invalid_datetime(self, date: datetime, delta: timedelta, subtract: bool = False) -> bool:
        """Check if the resultant `datetime` would exceed the bounds supported by `datetime`."""

        date_sec = date.timestamp()
        delta_sec = delta.total_seconds()

        # datetime.min and datetime.max error on Windows when using .timestamp()
        # so it is necessary to manually create the datetime objects.
        min_datetime_timestamp = datetime(1, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc).timestamp()
        max_datetime_timestamp = datetime(9999, 12, 31, 23, 59, 59, 999999, tzinfo=timezone.utc).timestamp()

        return (
            (date_sec + delta_sec < min_datetime_timestamp or date_sec + delta_sec > max_datetime_timestamp)
            if not subtract
            else (date_sec - delta_sec < min_datetime_timestamp or date_sec - delta_sec > max_datetime_timestamp)
        )

    def _invalid_timedelta(self, first: timedelta, second: timedelta, subtract: bool = False) -> bool:
        """Check if the resultant `timedelta` would exceed the bounds supported by `timedelta`."""

        first_sec = first.total_seconds()
        second_sec = second.total_seconds()

        return (
            (
                first_sec + second_sec < timedelta.min.total_seconds()
                or first_sec + second_sec > timedelta.max.total_seconds()
            )
            if not subtract
            else (
                first_sec - second_sec < timedelta.min.total_seconds()
                or first_sec - second_sec > timedelta.max.total_seconds()
            )
        )

    def _convert_to_hhmmss(self, seconds: int | float) -> str:
        """Convert the passed seconds to `Days, HH:MM:SS.MS` format."""

        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, remainder = divmod(remainder, 60)
        seconds, milliseconds = divmod(remainder, 1)
        decimal = round(milliseconds, 9)
        formatted = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

        if decimal:
            formatted += f".{str(decimal)[2:]}".rstrip("0").rstrip(".")

        if days > 0:
            return f"{int(days)} Day{'s' if days != 1 else ''}, {formatted}"
        else:
            return formatted

    def __str__(self) -> str:
        """Return `self.result.seconds` as a `Days, HH:MM:SS.MS` string."""
        return self._convert_to_hhmmss(self.result.seconds)

    def __repr__(self) -> str:
        """Return a string representation of the TimeLength with attributes included."""
        return f"TimeLength(content={json.dumps(self.content)}, locale={repr(self.locale)})"

    def __add__(self, other: TimeLength | timedelta | float | int) -> TimeLength:
        """---
        Get the absolute sum of `self` and a `TimeLength`, a `timedelta`, or a number.

        #### Arguments
        - other: `TimeLength | timedelta | float | int` — The object to add to `self`.

        #### Returns
        - A `TimeLength` that represents the absolute sum of `self` and the passed value.

        #### Raises
        - `NoValidScalesError` when no valid and enabled scales are found to perform the action.
        """

        base = self.locale.base_scale

        if isinstance(other, TimeLength):
            return TimeLength(
                content=f"{abs(self.result.seconds + other.result.seconds) / base.scale} {base.terms[0]}",
                locale=deepcopy(self.locale),
            )
        elif isinstance(other, timedelta):
            return TimeLength(
                content=f"{abs(self.result.seconds + other.total_seconds()) / base.scale} {base.terms[0]}",
                locale=deepcopy(self.locale),
            )
        elif isinstance(other, (float, int)):
            return TimeLength(
                content=f"{abs(self.result.seconds + other) / base.scale} {base.terms[0]}",
                locale=deepcopy(self.locale),
            )
        else:
            return NotImplemented

    def __radd__(self, other: datetime | timedelta) -> datetime | timedelta:
        """---
        Get the sum of a `datetime` or a `timedelta` and `self`.

        #### Arguments
        - other: `datetime | timedelta` — The object to add `self` to.

        #### Returns
        - A `datetime` in the future by the amount of `self.result.delta`.
        - A `timedelta` that represents the sum of the passed value and `self.result.delta`.

        #### Raises
        - `PotentialDateTimeError` when the resultant `datetime` would exceed the supported bounds of `datetime`.
        - `ParsedTimeDeltaError` when `self.result` is a value exceeding the supported bounds of `timedelta`.
        - `PotentialTimeDeltaError` when the resultant `timedelta` would exceed the supported bounds of `timedelta`.
        """

        if isinstance(other, datetime):
            return self.hence(other)
        elif isinstance(other, timedelta):
            if self.result.delta is None:
                raise ParsedTimeDeltaError
            elif self._invalid_timedelta(other, self.result.delta):
                raise PotentialTimeDeltaError

            return self.result.delta + other
        else:
            return NotImplemented

    def __sub__(self, other: TimeLength | timedelta | float | int) -> TimeLength:
        """---
        Get the absolute difference between `self` and a `TimeLength`, a `timedelta`, or a number.

        #### Arguments
        - other: `TimeLength | timedelta | float | int` — The object to subtract from `self`.

        #### Returns
        - A `TimeLength` that represents the absolute difference between `self` and the passed value.

        #### Raises
        - `NoValidScalesError` when no valid and enabled scales are found to perform the action.
        """

        base = self.locale.base_scale

        if isinstance(other, TimeLength):
            return TimeLength(
                content=f"{abs(self.result.seconds - other.result.seconds) / base.scale} {base.terms[0]}",
                locale=deepcopy(self.locale),
            )
        elif isinstance(other, timedelta):
            return TimeLength(
                content=f"{abs(self.result.seconds - other.total_seconds()) / base.scale} {base.terms[0]}",
                locale=deepcopy(self.locale),
            )
        elif isinstance(other, (float, int)):
            return TimeLength(
                content=f"{abs(self.result.seconds - other) / base.scale} {base.terms[0]}",
                locale=deepcopy(self.locale),
            )
        else:
            return NotImplemented

    def __rsub__(self, other: datetime | timedelta) -> datetime | timedelta:
        """
        Get the difference between a a `datetime` or a `timedelta` and `self`.

        #### Arguments
        - other: `datetime | timedelta` — The object to subtract `self` from.

        #### Returns
        - A `datetime` in the past by the amount of `self.result.delta`.
        - A `timedelta` that represents the difference between the passed value and `self.result.delta`.

        #### Raises
        - `PotentialDateTimeError` when the resultant `datetime` would exceed the supported bounds of `datetime`.
        - `ParsedTimeDeltaError` when `self.result` is a value exceeding the supported bounds of `timedelta`.
        - `PotentialTimeDeltaError` when the resultant `timedelta` would exceed the supported bounds of `timedelta`.
        """

        if isinstance(other, datetime):
            return self.ago(other)
        elif isinstance(other, timedelta):
            if self.result.delta is None:
                raise ParsedTimeDeltaError
            elif self._invalid_timedelta(other, self.result.delta, True):
                raise PotentialTimeDeltaError("The resultant timedelta would exceed the supported bounds of timedelta.")

            return other - self.result.delta
        else:
            return NotImplemented

    def __mul__(self, other: float | int) -> TimeLength:
        """
        Get the absolute multiplication of `self` and a number.

        #### Arguments
        - other: `float | int` — The number to multiply `self` by.

        #### Returns
        - A `TimeLength` that represents the absolute multiplication of `self` and the passed number.

        #### Raises
        - `NoValidScalesError` when no valid and enabled scales are found to perform the action.
        """

        if not isinstance(other, (float, int)):
            return NotImplemented

        base = self.locale.base_scale

        return TimeLength(
            content=f"{abs(self.result.seconds * other) / base.scale} {base.terms[0]}",
            locale=deepcopy(self.locale),
        )

    __rmul__ = __mul__

    def __truediv__(self, other: TimeLength | timedelta | float | int) -> TimeLength | float:
        """
        Get the division of `self` and a `TimeLength`, a `timedelta`, or a number.

        #### Arguments
        - other: `TimeLength | timedelta | float | int` — The object to divide `self` by.

        #### Returns
        - A `TimeLength` that represents the absolute division of `self` and the passed number.
        - A `float` that represents the division of `self` and the passed `TimeLength` or `timedelta`.

        #### Raises
        - `NoValidScalesError` when no valid and enabled scales are found to perform the action.
        """

        if isinstance(other, TimeLength):
            return self.result.seconds / other.result.seconds
        elif isinstance(other, timedelta):
            return self.result.seconds / other.total_seconds()
        elif isinstance(other, (float, int)):
            base = self.locale.base_scale

            return TimeLength(
                content=f"{abs(self.result.seconds / other) / base.scale} {base.terms[0]}",
                locale=deepcopy(self.locale),
            )
        else:
            return NotImplemented

    def __rtruediv__(self, other: timedelta) -> float:
        """
        Get the division of a `timedelta` and `self`.

        #### Arguments
        - other: `timedelta` — The object to divide by `self`.

        #### Returns
        - A `float` that represents the division of the passed `timedelta` and `self`.
        """

        if isinstance(other, timedelta):
            return other.total_seconds() / self.result.seconds
        else:
            return NotImplemented

    def __floordiv__(self, other: TimeLength | timedelta | float | int) -> TimeLength | float:
        """
        Get the floor division of `self` and a `TimeLength`, a `timedelta`, or a number.

        #### Arguments
        - other: `TimeLength | timedelta | float | int` — The object to divide `self` by.

        #### Returns
        - A `TimeLength` that represents the absolute floor division of `self` and the passed number.
        - A `float` that represents the floor division of `self` and the passed `TimeLength` or `timedelta`.

        #### Raises
        - `NoValidScalesError` when no valid and enabled scales are found to perform the action.
        """

        if isinstance(other, TimeLength):
            return int(self.result.seconds // other.result.seconds)
        elif isinstance(other, timedelta):
            return int(self.result.seconds // other.total_seconds())
        elif isinstance(other, (float, int)):
            base = self.locale.base_scale

            return TimeLength(
                content=f"{abs(self.result.seconds // other) / base.scale} {base.terms[0]}",
                locale=deepcopy(self.locale),
            )
        else:
            return NotImplemented

    def __rfloordiv__(self, other: timedelta) -> float:
        """
        Get the floor division of a `timedelta` and `self`.

        #### Arguments
        - other: `timedelta` — The object to divide by `self`.

        #### Returns
        - A `float` that represents the floor division of the passed `timedelta` and `self`.
        """

        if isinstance(other, timedelta):
            return int(other.total_seconds() // self.result.seconds)
        else:
            return NotImplemented

    def __mod__(self, other: TimeLength | timedelta | float | int) -> TimeLength:
        """
        Get the absolute modulo of `self` and a `TimeLength`, `timedelta`, or a number.

        #### Arguments
        - other: `TimeLength | timedelta | float | int` — The object to modulo `self` by.

        #### Returns
        - A `TimeLength` that represents the modulo of `self` and the passed `TimeLength`, `timedelta`, or number.

        #### Raises
        - `NoValidScalesError` when no valid and enabled scales are found to perform the action.
        """

        base = self.locale.base_scale

        if isinstance(other, TimeLength):
            return TimeLength(
                content=f"{abs(self.result.seconds % other.result.seconds) / base.scale} {base.terms[0]}",
                locale=deepcopy(self.locale),
            )
        elif isinstance(other, timedelta):
            return TimeLength(
                content=f"{abs(self.result.seconds % other.total_seconds()) / base.scale} {base.terms[0]}",
                locale=deepcopy(self.locale),
            )
        elif isinstance(other, (float, int)):
            return TimeLength(
                content=f"{abs(self.result.seconds % other) / base.scale} {base.terms[0]}",
                locale=deepcopy(self.locale),
            )
        else:
            return NotImplemented

    def __rmod__(self, other: timedelta) -> timedelta:
        """
        Get the modulo of a `TimeLength` or `timedelta` and `self`.

        #### Arguments
        - other: `timedelta` — The object to modulo by `self`.

        #### Returns
        - A timedelta that represents the modulo of the passed `timedelta` and `self`.

        #### Raises
        - `ParsedTimeDeltaError` when `self.result` is a value exceeding the supported bounds of `timedelta`.
        """

        if isinstance(other, timedelta):
            if self.result.delta is None:
                raise ParsedTimeDeltaError

            return other % self.result.delta
        else:
            return NotImplemented

    def __divmod__(self, other: TimeLength | timedelta | float | int) -> tuple[float, TimeLength]:
        """
        Get the divmod of `self` and a `TimeLength`, `timedelta`, or a number.

        #### Arguments
        - other: `TimeLength | timedelta | float | int` — The object to divmod `self` by.

        #### Returns
        - A tuple of a `float` and an absolute `TimeLength` that represent the divmod of `self` and the passed
            `TimeLength`, `timedelta`, or number.
        """

        if isinstance(other, TimeLength):
            return (
                self.result.seconds // other.result.seconds,
                self % other,
            )
        elif isinstance(other, timedelta):
            return (
                self.result.seconds // other.total_seconds(),
                self % other,
            )
        elif isinstance(other, (float, int)):
            return (
                self.result.seconds // other,
                self % other,
            )
        else:
            return NotImplemented

    def __rdivmod__(self, other: timedelta) -> tuple[float, timedelta]:
        """
        Get the divmod of a `timedelta` and `self`.

        #### Arguments
        - other: `timedelta` — The object to divmod by `self`.

        #### Returns
        - A tuple of a `float` and a `timedelta` that represent the divmod of the passed `timedelta` and `self`.
        """

        if isinstance(other, timedelta):
            return (
                other.total_seconds() // self.result.seconds,
                other % self,
            )
        else:
            return NotImplemented

    def __pow__(self, other: float | int, mod: TimeLength | timedelta | float | int | None = None) -> TimeLength:
        """
        Get the absolute power of `self` and a number.

        #### Arguments
        - other: `float | int` — The number to raise `self` to.
        - mod: `TimeLength | timedelta | float | int = None` — The object to modulo the result by.

        #### Returns
        - A `TimeLength` that represents the absolute power of `self` and the passed number, optionally moduloed by mod.

        #### Raises
        - `NoValidScalesError` when no valid and enabled scales are found to perform the action.
        """

        if not isinstance(other, (float, int)):
            return NotImplemented
        elif mod is not None and not isinstance(mod, (TimeLength, timedelta, float, int)):
            return NotImplemented

        if not mod:
            result: float = abs(self.result.seconds**other)
        else:
            mod_seconds: float = (
                mod.result.seconds
                if isinstance(mod, TimeLength)
                else mod.total_seconds()
                if isinstance(mod, timedelta)
                else mod
            )
            result: float = abs(self.result.seconds**other) % mod_seconds

        base = self.locale.base_scale

        return TimeLength(
            content=f"{result / base.scale} {base.terms[0]}",
            locale=deepcopy(self.locale),
        )

    def __bool__(self) -> bool:
        """Return if the parsing succeeded."""
        return self.result.success

    def __len__(self) -> int:
        """Return the length of `self.content`."""
        return len(self.content)

    def __abs__(self) -> TimeLength:
        """Return `self` unchanged as `TimeLength` is an absolute measurement."""
        return self

    def __pos__(self) -> TimeLength:
        """Return `self` unchanged as `TimeLength` is an absolute measurement."""
        return self

    def __neg__(self) -> TimeLength:
        """Return `self` unchanged as `TimeLength` is an absolute measurement."""
        return self

    def __gt__(self, other: TimeLength | timedelta | float | int) -> bool:
        """
        Check if `self` is greater than `other`.

        #### Arguments
        - other: `TimeLength | timedelta | float | int` — The object to compare to.

        #### Returns
        - A `bool` indicating if `self` is greater than `other` based on their seconds.
        """

        if not isinstance(other, (TimeLength, timedelta, float, int)):
            return NotImplemented

        other_seconds = (
            other.result.seconds
            if isinstance(other, TimeLength)
            else other.total_seconds()
            if isinstance(other, timedelta)
            else other
        )

        return self.result.seconds > other_seconds

    def __ge__(self, other: TimeLength | timedelta | float | int) -> bool:
        """
        Check if `self` is greater than or equal to other.

        #### Arguments
        - other: `TimeLength | timedelta | float | int` — The object to compare to.

        #### Returns
        - A `bool` indicating if `self` is greater than or equal to `other` based on their seconds.
        """

        if not isinstance(other, (TimeLength, timedelta, float, int)):
            return NotImplemented

        other_seconds = (
            other.result.seconds
            if isinstance(other, TimeLength)
            else other.total_seconds()
            if isinstance(other, timedelta)
            else other
        )

        return self.result.seconds >= other_seconds

    def __lt__(self, other: TimeLength | timedelta | float | int) -> bool:
        """
        Check if `self` is less than `other`.

        #### Arguments
        - other: `TimeLength | timedelta | float | int` — The object to compare to.

        #### Returns
        - A `bool` indicating if `self` is less than `other` based on their seconds.
        """

        if not isinstance(other, (TimeLength, timedelta, float, int)):
            return NotImplemented

        other_seconds = (
            other.result.seconds
            if isinstance(other, TimeLength)
            else other.total_seconds()
            if isinstance(other, timedelta)
            else other
        )

        return self.result.seconds < other_seconds

    def __le__(self, other: TimeLength | timedelta | float | int) -> bool:
        """
        Check if `self` is less than or equal to `other`.

        #### Arguments
        - other: `TimeLength | timedelta | float | int` — The object to compare to.

        #### Returns
        - A `bool` indicating if `self` is less than or equal to `other` based on their seconds.
        """

        if not isinstance(other, (TimeLength, timedelta, float, int)):
            return NotImplemented

        other_seconds = (
            other.result.seconds
            if isinstance(other, TimeLength)
            else other.total_seconds()
            if isinstance(other, timedelta)
            else other
        )

        return self.result.seconds <= other_seconds

    def __eq__(self, other: object) -> bool:
        """
        Check if `self` is equal to `other`.

        #### Arguments
        - other: `TimeLength | timedelta | float | int` — The object to compare to.

        #### Returns
        - A `bool` indicating if `self` is equal to `other` based on their seconds.
        """

        if not isinstance(other, (TimeLength, timedelta, float, int)):
            return False

        other_seconds = (
            other.result.seconds
            if isinstance(other, TimeLength)
            else other.total_seconds()
            if isinstance(other, timedelta)
            else other
        )

        return self.result.seconds == other_seconds

    def __ne__(self, other: object) -> bool:
        """
        Check if `self` is not equal to `other`.

        #### Arguments
        - other: `TimeLength | timedelta | float | int` — The object to compare to.

        #### Returns
        - A `bool` indicating if `self` is not equal to `other` based on their seconds.
        """

        if not isinstance(other, (TimeLength, timedelta, float, int)):
            return True

        other_seconds = (
            other.result.seconds
            if isinstance(other, TimeLength)
            else other.total_seconds()
            if isinstance(other, timedelta)
            else other
        )

        return self.result.seconds != other_seconds
