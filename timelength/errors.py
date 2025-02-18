from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from timelength.locales import Locale


class PotentialDateTimeError(OverflowError):
    """Exception for when a `datetime` would be invalid if attempted."""

    def __init__(self, message: str = "") -> None:
        default_message = "The parsed value exceeds the bounds supported by datetime."
        message = message or default_message
        super().__init__(message)


class ParsedTimeDeltaError(OverflowError):
    """Exception for when the parsed result exceeds the bounds supported by `timedelta`."""

    def __init__(self, message: str = "") -> None:
        default_message = "The parsed value exceeds the bounds supported by timedelta."
        message = message or default_message
        super().__init__(message)


class PotentialTimeDeltaError(OverflowError):
    """Exception for when a `timedelta` would be invalid if attempted."""

    def __init__(self, message: str = "") -> None:
        default_message = "The parsed value exceeds the bounds supported by timedelta."
        message = message or default_message
        super().__init__(message)


class InvalidScaleError(ValueError):
    """Exception for when a `Scale` is invalid."""

    def __init__(self, scale_name: str = "", message="") -> None:
        default_message = "A scale is missing required attributes."

        if scale_name and not message:
            message = f'"{scale_name}" is missing required attributes.'
        else:
            message = message or default_message

        super().__init__(message)
        self.scale_name = scale_name


class NoValidScalesError(ValueError):
    """Exception for when no `Scale` is valid."""

    def __init__(self, message: str = "") -> None:
        default_message = "No valid and enabled scales found."
        message = message or default_message
        super().__init__(message)


class InvalidNumeralError(ValueError):
    """Exception for when a `Numeral` is invalid."""

    def __init__(self, numeral_name: str = "", message: str = "") -> None:
        default_message = "A numeral is missing required attributes."

        if numeral_name and not message:
            message = f'"{numeral_name}" is missing required attributes.'
        else:
            message = message or default_message

        super().__init__(message)
        self.numeral_name = numeral_name


class NotALocaleError(ValueError):
    """Exception for when a `Locale` or `Guess` is not provided."""

    def __init__(self, invalid_locale: Any, message: str = "") -> None:
        default_message = f'"{type(invalid_locale).__name__}" is not an instance of Locale or Guess.'
        message = message or default_message
        super().__init__(message)


class InvalidLocaleError(ValueError):
    """Exception for when a `Locale` has invalid configuration."""

    def __init__(self, locale: Locale, message: str = "") -> None:
        message = message or f"The configuration for {repr(str(locale))} is invalid."
        super().__init__(message)


class InvalidParserError(ValueError):
    """Exception for when a parser is invalid."""

    def __init__(self, locale: Locale, message: str = "") -> None:
        message = message or f"{repr(str(locale))} is missing a valid parser function."
        super().__init__(message)
