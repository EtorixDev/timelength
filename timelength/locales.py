from __future__ import annotations

import json
import os
from importlib import util

from timelength.dataclasses import ParserSettings, Scale
from timelength.enums import FailureFlags, NumeralType
from timelength.errors import LocaleConfigError


class Locale:
    """
    Represents a default Locale, each of which may handle parsing differently.

    ### Attributes

    - `json_location` (`str`): The string path to the config file for this Locale.

    ### Methods
    - `__str__`: Return the name of the `Locale`.
    - `__repr__`: Return a string representation of the `Locale` with the config path included.
    """

    def __init__(
        self,
        json_location: str = "english.json",
        flags: FailureFlags = FailureFlags.NONE,
        settings: ParserSettings = ParserSettings(),
    ):
        """Initialize the `Locale` based on the passed config file."""
        self.flags: FailureFlags = flags
        self.settings: ParserSettings = settings
        self._json_location = json_location
        self._config = {}
        base_dir = os.path.dirname(__file__)

        locale_path = os.path.join(base_dir, "locales", json_location)
        if os.path.exists(locale_path):
            full_json_path = locale_path
        else:
            full_json_path = json_location
        self._load_config(full_json_path)

        if not self._config:
            raise LocaleConfigError("Provided config is empty.")

        self._parser_file = self._get_config_or_raise("parser_file")
        self._parser = None
        self._load_parser(base_dir)

        self._connectors = self._get_config_or_raise("connectors")
        self._segmentors = self._get_config_or_raise("segmentors")
        if not self._connectors or not self._segmentors:
            raise LocaleConfigError("Connectors and Segmentors must have at least one value in the config.")
        if set(self._connectors).intersection(self._segmentors):
            raise LocaleConfigError("Connectors and Segmentors may not have overlap in the config.")

        # _allowed_terms may appear ONCE in a row in the input while strict is enabled.
        # They may not appear in the middle of a segment/sentence, i.e interrupting a value/scale pair.
        self._allowed_terms = self._get_config_or_raise("allowed_terms")
        self._hhmmss_delimiters = self._get_config_or_raise("hhmmss_delimiters")
        self._decimal_delimiters = self._get_config_or_raise("decimal_delimiters")
        self._thousand_delimiters = self._get_config_or_raise("thousand_delimiters")
        all_delimiters = self._hhmmss_delimiters + self._decimal_delimiters + self._thousand_delimiters
        if len(all_delimiters) != len(set(all_delimiters)):
            raise LocaleConfigError("Delimiters may not have overlap in the config.")

        self._specials: list[str] = list(
            set(
                self._connectors
                + self._segmentors
                + self._allowed_terms
                + self._hhmmss_delimiters
                + self._decimal_delimiters
                + self._thousand_delimiters
            )
        )

        # Default Scales can be disabled by removing them from the config. In their place an empty Scale of
        # scale 0 will be added. This will cause its related TimeLength conversion method, such as `to_minutes`,
        # to error as dividing by 0 is not allowed. Parsing wise, it will be ignored as the terms list is empty.
        scales_json = self._get_config_or_raise("scales")
        self._millisecond = Scale(**self._config["scales"]["millisecond"]) if "millisecond" in scales_json else Scale()
        self._second = Scale(**self._config["scales"]["second"]) if "second" in scales_json else Scale()
        self._minute = Scale(**self._config["scales"]["minute"]) if "minute" in scales_json else Scale()
        self._hour = Scale(**self._config["scales"]["hour"]) if "hour" in scales_json else Scale()
        self._day = Scale(**self._config["scales"]["day"]) if "day" in scales_json else Scale()
        self._week = Scale(**self._config["scales"]["week"]) if "week" in scales_json else Scale()
        self._month = Scale(**self._config["scales"]["month"]) if "month" in scales_json else Scale()
        self._year = Scale(**self._config["scales"]["year"]) if "year" in scales_json else Scale()
        self._decade = Scale(**self._config["scales"]["decade"]) if "decade" in scales_json else Scale()
        self._century = Scale(**self._config["scales"]["century"]) if "century" in scales_json else Scale()
        scales: list[Scale] = [
            self._millisecond,
            self._second,
            self._minute,
            self._hour,
            self._day,
            self._week,
            self._month,
            self._year,
            self._decade,
            self._century,
        ]
        self._scales = [scale for scale in scales if scale]

        # Allow for custom defined Scales.
        for scale_name in scales_json:
            if scale_name not in {
                "millisecond",
                "second",
                "minute",
                "hour",
                "day",
                "week",
                "month",
                "year",
                "decade",
                "century",
            }:
                custom_scale = Scale(**self._config["scales"][scale_name])
                setattr(self, f"_{scale_name}", custom_scale)
                self._scales.append(custom_scale)

        if not self._scales:
            raise LocaleConfigError("At least one scale must be enabled in the config.")

        for scale in self._scales:
            missing: list[str] = []

            if not scale.scale:
                missing.append("scale")
            if not scale.singular:
                missing.append("singular")
            if not scale.plural:
                missing.append("plural")
            if not scale.terms:
                missing.append("terms")

            if missing:
                raise LocaleConfigError(f"Scale {scale} is missing the following attributes: {missing}")

        self._numerals: dict[str, dict[str, NumeralType | float | list[str]]] = self._get_config_or_raise("numerals")
        for numeral in self._numerals:
            numeral_type = self._numerals[numeral]["type"]
            if numeral_type not in NumeralType.__members__:
                raise LocaleConfigError(f"Numeral type {numeral_type} is not a valid NumeralType.")
            self._numerals[numeral]["type"] = NumeralType(numeral_type)
        self._extra_data = self._get_config_or_raise("extra_data")

    def __str__(self):
        """Return the name of the `Locale`."""
        return f"{self.__class__.__name__}"

    def __repr__(self):
        """Return a string representation of the `Locale` with the config path included."""
        return f"{self.__str__()}(flags=({repr(self.flags)}), settings={repr(self.settings)})"

    def _get_scale(self, text: str) -> Scale | None:
        """Get the scale that contains a specific value in its terms list."""
        for scale in self._scales:
            scale: Scale
            if text in scale.terms:
                return scale
        return None

    def _get_numeral(self, text: str) -> dict[str, dict[str, NumeralType | float | list[str]]] | None:
        """Get a numeral that contains a specific value in its terms list."""
        numeral = {}
        for numeral in self._numerals:
            if text in self._numerals[numeral]["terms"]:
                return self._numerals[numeral]
        return None

    def _load_parser(self, base_dir):
        """Load the parser file linked in the config file into a method attached to the `Locale`."""
        if self._parser and callable(self._parser):
            return  # Parser already loaded for this locale.
        parser_path = os.path.join(base_dir, "parsers", self._parser_file)
        if os.path.exists(parser_path):
            full_parser_path = parser_path
        else:
            full_parser_path = self._parser_file
        module_name, _ = os.path.splitext(os.path.basename(full_parser_path))
        try:
            spec = util.spec_from_file_location(module_name, full_parser_path)
            if not spec:
                raise FileNotFoundError
            module = util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._parser = getattr(module, module_name, None)
            if not callable(self._parser):
                raise AttributeError
        except (ModuleNotFoundError, FileNotFoundError):
            self._parser = None
            raise LocaleConfigError(f"File not found: {self._parser_file}") from None
        except AttributeError:
            self._parser = None
            raise LocaleConfigError(f"Parser function not found: {module_name}") from None

    def _load_config(self, file: str):
        """Load the config from the provided path."""
        with open(file, "r", encoding="utf-8") as f:
            self._config = json.load(f)

    def _get_config_or_raise(self, key: str) -> str | float | list | dict:
        """Retrieve a value from the config or raise if the value is not found."""
        value = self._config.get(key)
        if value is None:
            raise LocaleConfigError(f'Provided config is malformed. No "{key}" key provided.')
        return value


class CustomLocale(Locale):
    """
    Represents a custom `Locale`.

    ### Attributes
    - `json_location` (`str`): The string path to the config file for this `Locale`.
    - `flags` (`FailureFlags`): The flags that will cause parsing to fail.
    - `settings` (`ParserSettings`): The settings for the parser.


    ### Methods
    - `__str__`: Return the name of the `Locale`.
    - `__repr__`: Return a string representation of the `Locale` with the config path included.
    """

    def __init__(
        self, json_location: str, flags: FailureFlags = FailureFlags.NONE, settings: ParserSettings = ParserSettings()
    ):
        super().__init__(json_location, flags, settings)


class English(Locale):
    """
    Represents the `English` `Locale`.

    ### Attributes
    - `flags` (`FailureFlags`): The flags that will cause parsing to fail.
    - `settings` (`ParserSettings`): The settings for the parser.

    ### Methods
    - `__str__`: Return the name of the `Locale`.
    - `__repr__`: Return a string representation of the `Locale` with the config path included.

    ### Available Flags
    - `NONE`
    - `ALL`
    - `MALFORMED_CONTENT`
    - `UNKNOWN_TERM`
    - `MALFORMED_DECIMAL`
    - `MALFORMED_THOUSAND`
    - `MALFORMED_HHMMSS`
    - `LONELY_VALUE`
    - `CONSECUTIVE_VALUE`
    - `LONELY_SCALE`
    - `LEADING_SCALE`
    - `DUPLICATE_SCALE`
    - `CONSECUTIVE_SCALE`
    - `CONSECUTIVE_CONNECTOR`
    - `CONSECUTIVE_SEGMENTORS`
    - `CONSECUTIVE_SPECIALS`
    - `MISPLACED_ALLOWED_TERM`
    - `UNUSED_MULTIPLIER`

    ### Available Settings
    - `assume_seconds`
    - `limit_allowed_terms`
    - `allow_duplicate_scales`
    - `allow_thousands_extra_digits`
    - `allow_thousands_lacking_digits`
    - `allow_decimals_lacking_digits`
    """

    def __init__(self, flags: FailureFlags = FailureFlags.NONE, settings: ParserSettings = ParserSettings()):
        super().__init__("english.json", flags, settings)


class Spanish(Locale):
    """
    Represents the `Spanish` `Locale`.

    ### Attributes
    - `flags` (`FailureFlags`): The flags that will cause parsing to fail.
    - `settings` (`ParserSettings`): The settings for the parser.

    ### Methods
    - `__str__`: Return the name of the `Locale`.
    - `__repr__`: Return a string representation of the `Locale` with the config path included.

    ### Available Flags
    - `NONE`
    - `ALL`
    - `MALFORMED_CONTENT`
    - `UNKNOWN_TERM`
    - `MALFORMED_DECIMAL`
    - `MALFORMED_THOUSAND`
    - `MALFORMED_HHMMSS`
    - `LONELY_VALUE`
    - `CONSECUTIVE_VALUE`
    - `LONELY_SCALE`
    - `LEADING_SCALE`
    - `DUPLICATE_SCALE`
    - `CONSECUTIVE_SCALE`
    - `CONSECUTIVE_CONNECTOR`
    - `CONSECUTIVE_SEGMENTORS`
    - `CONSECUTIVE_SPECIALS`
    - `MISPLACED_ALLOWED_TERM`
    - `UNUSED_MULTIPLIER`

    ### Available Settings
    - `assume_seconds`
    - `limit_allowed_terms`
    - `allow_duplicate_scales`
    - `allow_thousands_extra_digits`
    - `allow_thousands_lacking_digits`
    - `allow_decimals_lacking_digits`
    """

    def __init__(self, flags: FailureFlags = FailureFlags.NONE, settings: ParserSettings = ParserSettings()):
        super().__init__("spanish.json", flags, settings)


class Guess(Locale):
    """
    Represents an unknown `Locale`. Does not contain all of the attributes of a `Locale`. Should never be used
    as a final `Locale`, but instead an intermediary until a `Locale` is determined.

    ### Attributes
    - `flags` (`FailureFlags`): The flags that will cause parsing to fail.
    - `settings` (`ParserSettings`): The settings for the parser.

    ### Methods
    - `__str__`: Return the name of the `Locale`.
    - `__repr__`: Return a string representation of the `Locale` with the config path included.


    ### Available Flags
    All settings. The actual applicable settings will be applied to the final `Locale`.

    ### Available Settings
    All flags. The actual applicable flags will be applied to the final `Locale`.
    """

    def __init__(
        self,
        json_location: str = "english.json",
        flags: FailureFlags = FailureFlags.NONE,
        settings: ParserSettings = ParserSettings(),
    ):
        self._json_location = json_location
        self.flags: FailureFlags = flags
        self.settings: ParserSettings = settings


LOCALES: list[Locale] = [English, Spanish]
