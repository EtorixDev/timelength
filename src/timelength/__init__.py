"""A flexible Python duration parser for human-readable lengths of time."""

from importlib.metadata import version

from timelength.dataclasses import Numeral as Numeral
from timelength.dataclasses import ParsedTimeLength as ParsedTimeLength
from timelength.dataclasses import ParserSettings as ParserSettings
from timelength.dataclasses import Scale as Scale
from timelength.enums import FailureFlags as FailureFlags
from timelength.errors import InvalidLocaleError as InvalidLocaleError
from timelength.errors import InvalidNumeralError as InvalidNumeralError
from timelength.errors import InvalidParserError as InvalidParserError
from timelength.errors import InvalidScaleError as InvalidScaleError
from timelength.errors import NotALocaleError as NotALocaleError
from timelength.errors import NoValidScalesError as NoValidScalesError
from timelength.errors import ParsedTimeDeltaError as ParsedTimeDeltaError
from timelength.errors import PotentialDateTimeError as PotentialDateTimeError
from timelength.errors import PotentialTimeDeltaError as PotentialTimeDeltaError
from timelength.locales import English as English
from timelength.locales import Guess as Guess
from timelength.locales import Locale as Locale
from timelength.locales import Spanish as Spanish
from timelength.timelength import TimeLength as TimeLength

__version__ = version("timelength")

__all__ = [
    "English",
    "FailureFlags",
    "Guess",
    "InvalidLocaleError",
    "InvalidNumeralError",
    "InvalidParserError",
    "InvalidScaleError",
    "Locale",
    "NoValidScalesError",
    "NotALocaleError",
    "Numeral",
    "ParsedTimeDeltaError",
    "ParsedTimeLength",
    "ParserSettings",
    "PotentialDateTimeError",
    "PotentialTimeDeltaError",
    "Scale",
    "Spanish",
    "TimeLength",
    "__version__",
]
