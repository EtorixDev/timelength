"""A flexible python duration parser designed for human readable lengths of time."""

from timelength.dataclasses import Numeral as Numeral
from timelength.dataclasses import ParsedTimeLength as ParsedTimeLength
from timelength.dataclasses import ParserSettings as ParserSettings
from timelength.dataclasses import Scale as Scale
from timelength.enums import FailureFlags as FailureFlags
from timelength.errors import (
    InvalidLocaleError as InvalidLocaleError,
    InvalidNumeralError as InvalidNumeralError,
    InvalidParserError as InvalidParserError,
    InvalidScaleError as InvalidScaleError,
    NotALocaleError as NotALocaleError,
    NoValidScalesError as NoValidScalesError,
    ParsedTimeDeltaError as ParsedTimeDeltaError,
    PotentialDateTimeError as PotentialDateTimeError,
    PotentialTimeDeltaError as PotentialTimeDeltaError,
)
from timelength.locales import English as English
from timelength.locales import Guess as Guess
from timelength.locales import Locale as Locale
from timelength.locales import Spanish as Spanish
from timelength.timelength import TimeLength as TimeLength

__all__ = [
    "Numeral",
    "ParsedTimeLength",
    "ParserSettings",
    "Scale",
    "FailureFlags",
    "InvalidLocaleError",
    "InvalidNumeralError",
    "InvalidParserError",
    "InvalidScaleError",
    "NotALocaleError",
    "NoValidScalesError",
    "ParsedTimeDeltaError",
    "PotentialDateTimeError",
    "PotentialTimeDeltaError",
    "English",
    "Guess",
    "Locale",
    "Spanish",
    "TimeLength",
]
