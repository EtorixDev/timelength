"""A flexible python duration parser designed for human readable lengths of time."""

from timelength.dataclasses import Numeral, ParsedTimeLength, ParserSettings, Scale
from timelength.enums import FailureFlags
from timelength.errors import (
    InvalidLocaleError,
    InvalidNumeralError,
    InvalidParserError,
    InvalidScaleError,
    NotALocaleError,
    NoValidScalesError,
    ParsedTimeDeltaError,
    PotentialDateTimeError,
    PotentialTimeDeltaError,
)
from timelength.locales import English, Guess, Locale, Spanish
from timelength.timelength import TimeLength
