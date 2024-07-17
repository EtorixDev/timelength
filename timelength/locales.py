from __future__ import annotations

import json
import os
from fractions import Fraction
from importlib import util

from timelength.dataclasses import Numeral, ParserSettings, Scale
from timelength.enums import FailureFlags, NumeralType
from timelength.errors import LocaleConfigError


class Locale:
    """
    Represents a `Locale` context used for parsing lengths of time.

    #### Attributes
    - json_location: `str | os.PathLike = "english.json"` — The path to the config file for this `Locale`.
    - flags: `FailureFlags | None = None` — The flags that will cause parsing to fail.
        - If passed, flags loaded from the config will be overwritten.
    - settings: `ParserSettings | None = None` — The settings for the parser.
        - If passed, settings loaded from the config will be overwritten.

    #### Methods
    - `validate()` — Validate the values for config attributes.
        - Automatically called during initialization. Manually call this method again if internal attributes are
            changed.
    - `get_scale()` — Get the scale that contains a specific value in its terms list, if any.
    - `get_numeral()` — Get a numeral that contains a specific value in its terms list, if any.

    #### Raises
    - `LocaleConfigError` — Raised when the config at `json_location` does not exist or is malformed.
    """

    def __init__(
        self,
        json_location: str | os.PathLike = "english.json",
        flags: FailureFlags | None = None,
        settings: ParserSettings | None = None,
    ):
        self._json_location = os.fspath(json_location) if isinstance(json_location, os.PathLike) else json_location
        self._config = {}

        base_dir: str = os.path.dirname(__file__)
        locale_path: str = os.path.join(base_dir, "locales", self._json_location)
        full_json_path: str = locale_path if os.path.exists(locale_path) else self._json_location
        if not os.path.exists(full_json_path):
            raise LocaleConfigError(f'The provided config does not exist: "{full_json_path}"')

        self._load_config(full_json_path)
        if not self._config:
            raise LocaleConfigError("The provided config is empty.")

        self._parser_file: str = self._get_config_or_raise("parser_file")
        self._parser = None
        self._load_parser(base_dir)

        self.flags: FailureFlags = flags
        if not flags:
            flags_json = self._get_config_or_raise("flags")
            if not isinstance(flags_json, list):
                raise LocaleConfigError("Invalid flag json provided in config.")

            combined_flags = FailureFlags(0)
            for flag in flags_json:
                try:
                    combined_flags |= FailureFlags[flag]
                except KeyError as e:
                    raise LocaleConfigError(f"Invalid flag provided in config: {flag}") from e

            self.flags = combined_flags

        self.settings: ParserSettings = settings
        if not settings:
            settings_json = self._get_config_or_raise("settings")
            try:
                self.settings = ParserSettings(**settings_json)
            except TypeError as e:
                key_name = str(e).split("'")[1]
                raise LocaleConfigError(f"Invalid setting provided in config: {key_name}") from e

        self._connectors: list[str] = self._get_config_or_raise("connectors")
        self._segmentors: list[str] = self._get_config_or_raise("segmentors")

        self._allowed_terms: list[str] = self._get_config_or_raise("allowed_terms")
        self._hhmmss_delimiters: list[str] = self._get_config_or_raise("hhmmss_delimiters")
        self._decimal_delimiters: list[str] = self._get_config_or_raise("decimal_delimiters")
        self._thousand_delimiters: list[str] = self._get_config_or_raise("thousand_delimiters")

        # Scales can be disabled by removing them from the config or by setting their values to 0. This will cause the
        # related conversion methods, such as `to_minutes`, to error. Disabled scales will be ignored during parsing.
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
        self._all_scales: list[Scale] = [
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
                self._all_scales.append(custom_scale)
                setattr(self, f"{scale_name}", custom_scale)

        numerals_json: dict[str, dict[str, str | float | list[str]]] = self._get_config_or_raise("numerals")
        self._all_numerals: list[Numeral] = []
        for numeral in numerals_json:
            name: str = numeral

            raw_type: str = numerals_json[numeral]["type"]
            try:
                type: NumeralType | None = NumeralType(raw_type) if raw_type else None
            except ValueError as e:
                raise LocaleConfigError(f'Numeral type "{type}" is not a valid NumeralType.') from e

            value: float = (
                float(Fraction(numerals_json[numeral]["value"]))
                if isinstance(numerals_json[numeral]["value"], str)
                else float(numerals_json[numeral]["value"])
            )

            terms: list[str] = numerals_json[numeral]["terms"]
            self._all_numerals.append(Numeral(name, type, value, terms))

        self._extra_data = self._get_config_or_raise("extra_data")

        self.validate()

    @property
    def _numerals(self) -> list[Numeral]:
        return [numeral for numeral in self._all_numerals if numeral.enabled]

    @property
    def _scales(self) -> list[Scale]:
        """Return a list of all enabled scales."""
        return [scale for scale in self._all_scales if scale.enabled]

    @property
    def _specials(self) -> list[str]:
        """Return a list of all special terms in the config."""
        return list(
            set(
                self._connectors
                + self._segmentors
                + self._allowed_terms
                + self._hhmmss_delimiters
                + self._decimal_delimiters
                + self._thousand_delimiters
            )
        )

    def __str__(self) -> str:
        """Return the name of `self`."""
        return f"{self.__class__.__name__}"

    def __repr__(self) -> str:
        """Return a string representation of `self` with attributes included."""
        return f"{self.__str__()}(json_location={repr(self._json_location).replace("'", '"')}, flags=({repr(self.flags)}), settings={repr(self.settings)})"

    def _validate_connectors_segmentors(self) -> bool:
        """Validate the values for the connectors and segmentors in the config."""
        if not self._connectors or not self._segmentors:
            raise LocaleConfigError("Connectors and Segmentors must have at least one value in the config.")
        elif set(self._connectors).intersection(self._segmentors):
            raise LocaleConfigError("Connectors and Segmentors may not have overlap in the config.")

        return True

    def _validate_delimiters(self) -> bool:
        """Validate the values for the delimiters in the config."""
        all_delimiters = self._hhmmss_delimiters + self._decimal_delimiters + self._thousand_delimiters

        if len(all_delimiters) != len(set(all_delimiters)):
            raise LocaleConfigError("Delimiters may not have overlap in the config.")

        return True

    def _validate_scales(self) -> bool:
        """Validate the values for the scales in the config."""
        if not self._scales:
            raise LocaleConfigError("At least one scale must be enabled in the config.")

        return True

    def _validate_numerals(self) -> bool:
        """Validate the values for the NumeralType enum in the config."""
        for numeral in self._numerals:
            if not numeral.type:
                raise LocaleConfigError(
                    f"Numeral {numeral.name} must have a NumeralType."
                    if numeral.name
                    else "All numerals must have a NumeralType."
                )
            elif numeral.type.name not in NumeralType.__members__:
                raise LocaleConfigError(f"Numeral type {numeral.type} is not a valid NumeralType.")

        return True

    def validate(self) -> bool:
        """
        Validate the values for config attributes. Returns `True` on success.

        #### Raises
        - `LocaleConfigError`: The config is malformed.
        """

        self._validate_connectors_segmentors()
        self._validate_delimiters()
        self._validate_scales()
        self._validate_numerals()

        return True

    def get_scale(self, text: str) -> Scale | None:
        """Get the scale that contains a specific value in its terms list."""
        for scale in self._scales:
            if text in scale.terms:
                return scale

        return None

    def get_numeral(self, text: str) -> Numeral | None:
        """Get a numeral that contains a specific value in its terms list."""
        numeral = {}
        for numeral in self._numerals:
            if text in numeral.terms:
                return numeral

        return None

    def _load_parser(self, base_dir) -> None:
        """Load the parser file linked in the config file into a method attached to the `Locale`."""
        if self._parser and callable(self._parser):
            return

        parser_path = os.path.join(base_dir, "parsers", self._parser_file)
        full_parser_path = parser_path if os.path.exists(parser_path) else self._parser_file
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
        except (ModuleNotFoundError, FileNotFoundError) as e:
            self._parser = None
            raise LocaleConfigError(f"File not found: {self._parser_file}") from e
        except AttributeError as e:
            self._parser = None
            raise LocaleConfigError(f"Parser function not found: {module_name}") from e

    def _load_config(self, file: str) -> None:
        """Load the config from the provided path."""
        with open(file, "r", encoding="utf-8") as f:
            self._config = json.load(f)

    def _get_config_or_raise(self, key: str) -> str | float | list | dict:
        """Retrieve a value from the config or raise `LocaleConfigError` if the value is not found."""
        value = self._config.get(key)
        if value is None:
            raise LocaleConfigError(f'Provided config is malformed. No "{key}" key provided.')

        return value


class English(Locale):
    """
    Represents the `English` context used for parsing lengths of time.

    #### Attributes
    - flags: `FailureFlags | None = None` — The flags that will cause parsing to fail.
        - If passed, flags loaded from the config will be overwritten.
    - settings: `ParserSettings | None = None` — The settings for the parser.
        - If passed, settings loaded from the config will be overwritten.

    #### Methods
    - `validate()` — Validate the values for config attributes.
        - Automatically called during initialization. Manually call this method again if internal attributes are
            changed.
    - `get_scale()` — Get the scale that contains a specific value in its terms list, if any.
    - `get_numeral()` — Get a numeral that contains a specific value in its terms list, if any.

    #### Available Flags
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

    #### Available Settings
    - `assume_seconds`
    - `limit_allowed_terms`
    - `allow_duplicate_scales`
    - `allow_thousands_extra_digits`
    - `allow_thousands_lacking_digits`
    - `allow_decimals_lacking_digits`

    #### Raises
    - `LocaleConfigError` — Raised when "english.json" does not exist or is malformed.
    """

    def __init__(self, flags: FailureFlags | None = None, settings: ParserSettings | None = None):
        super().__init__("english.json", flags, settings)

    def __repr__(self):
        """Return a string representation of `self` with attributes included."""
        return f"{self.__str__()}(flags=({repr(self.flags)}), settings={repr(self.settings)})"


class Spanish(Locale):
    """
    Represents the `Spanish` context used for parsing lengths of time.

    #### Attributes
    - flags: `FailureFlags | None = None` — The flags that will cause parsing to fail.
        - If passed, flags loaded from the config will be overwritten.
    - settings: `ParserSettings | None = None` — The settings for the parser.
        - If passed, settings loaded from the config will be overwritten.

    #### Methods
    - `validate()` — Validate the values for config attributes.
        - Automatically called during initialization. Manually call this method again if internal attributes are
            changed.
    - `get_scale()` — Get the scale that contains a specific value in its terms list, if any.
    - `get_numeral()` — Get a numeral that contains a specific value in its terms list, if any.

    #### Available Flags
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

    #### Available Settings
    - `assume_seconds`
    - `limit_allowed_terms`
    - `allow_duplicate_scales`
    - `allow_thousands_extra_digits`
    - `allow_thousands_lacking_digits`
    - `allow_decimals_lacking_digits`

    #### Raises
    - `LocaleConfigError` — Raised when "spanish.json" does not exist or is malformed.
    """

    def __init__(self, flags: FailureFlags | None = None, settings: ParserSettings | None = None):
        super().__init__("spanish.json", flags, settings)

    def __repr__(self):
        """Return a string representation of `self` with attributes included."""
        return f"{self.__str__()}(flags=({repr(self.flags)}), settings={repr(self.settings)})"


class Guess(Locale):
    """
    Represents an unknown `Locale` context used for parsing lengths of time.

    Does not contain all of the attributes of a `Locale`. Should never be used as a final `Locale`, but instead an
    intermediary until a `Locale` is determined.

    #### Attributes
    - flags: `FailureFlags | None = None` — The flags that will cause parsing to fail.
        - If passed, flags loaded from the config will be overwritten.
    - settings: `ParserSettings | None = None` — The settings for the parser.
        - If passed, settings loaded from the config will be overwritten.

    #### Available Flags
    All flags. The actual applicable flags will be applied to the final `Locale`.

    #### Available Settings
    All settings. The actual applicable settings will be applied to the final `Locale`.

    #### Raises
    - `LocaleConfigError` — Raised if any of the locale configs are malformed or missing.
    """

    def __init__(
        self,
        flags: FailureFlags | None = None,
        settings: ParserSettings | None = None,
    ):
        self.flags: FailureFlags | None = flags
        self.settings: ParserSettings | None = settings

    def __repr__(self):
        """Return a string representation of `self` with attributes included."""
        return f"{self.__str__()}(flags={f'({repr(self.flags)})' if self.flags else None}, settings={repr(self.settings) if self.settings else None})"


LOCALES: list[Locale] = [English, Spanish]
