"""A Python package to parse human readable lengths of time."""

from timelength.dataclasses import ParserSettings
from timelength.enums import FailureFlags
from timelength.locales import LOCALES, CustomLocale, English, Guess, Spanish
from timelength.timelength import TimeLength
