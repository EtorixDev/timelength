from __future__ import annotations

import json
import os
from fractions import Fraction
from importlib import util
from typing import Any, Callable

from timelength.dataclasses import Numeral, ParsedTimeLength, ParserSettings, Scale
from timelength.enums import FailureFlags, NumeralType
from timelength.errors import (
    InvalidLocaleError,
    InvalidNumeralError,
    InvalidParserError,
    InvalidScaleError,
    NoValidScalesError,
)


class Locale:
    """---
    Represents a `Locale` context used for parsing lengths of time.

    #### Attributes
    - config_location: `str | os.PathLike = "english.json"` — The path to the config file for this `Locale`.
    - flags: `FailureFlags | None = None` — The flags that will cause parsing to fail.
        - If passed, flags loaded from the config will be overwritten.
    - settings: `ParserSettings | None = None` — The settings for the parser.
        - If passed, settings loaded from the config will be overwritten.

    #### Properties
    - `parser` — Return the parser function attached to the Locale.
    - `connectors` — Return the connectors if valid.
    - `segmentors` — Return the segmentors if valid.
    - `allowed_terms` — Return the allowed terms.
    - `hhmmss_delimiters` — Return the hhmmss delimiters if valid.
    - `decimal_delimiters` — Return the decimal delimiters if valid.
    - `thousand_delimiters` — Return the thousand delimiters if valid.
    - `fraction_delimiters` — Return the fraction delimiters if valid.
    - `delimiters` — Return a list of all delimiters if valid.
    - `specials` — Return a list of all special characters.
    - `usable_scales` — Return a list of valid and enabled scales.
    - `usable_numerals` — Return a list of valid and enabled numerals.
    - `base_scale` — Return the base scale for the locale.

    #### Methods
    - `get_scale()` — Get the scale that contains a specific value in its terms list, if any.
    - `get_numeral()` — Get the numeral that contains a specific value in its terms list, if any.

    #### Raises
    - `InvalidLocaleError` when the config at `config_location` does not exist or is malformed.
    - `InvalidParserError` when `self.parser` is not callable.
    - `NoValidScalesError` when no `Scale` is valid during validation.
    - `InvalidScaleError` when a `Scale` is invalid during initialization.
    - `InvalidNumeralError` when a `Numeral` is invalid during initialization.
    """

    def __init__(
        self,
        config_location: str | os.PathLike[str] = "english.json",
        flags: FailureFlags | None = None,
        settings: ParserSettings | None = None,
    ) -> None:
        self._config_location: str = (
            os.fspath(config_location) if isinstance(config_location, os.PathLike) else config_location
        )
        base_dir: str = os.path.dirname(__file__)
        locale_path: str = os.path.join(base_dir, "locales", self._config_location)
        full_json_path: str = locale_path if os.path.exists(locale_path) else self._config_location
        self._config: dict[str, Any] = self._load_config(full_json_path)

        self._parser_file: str = self._get_config_or_raise("parser_file", str)
        self._parser: Callable[[str, Locale], ParsedTimeLength] = self._load_parser(base_dir)

        self.flags: FailureFlags = self._load_flags(flags)
        self.settings: ParserSettings = self._load_settings(settings)

        self._connectors: list[str] = self._get_config_or_raise("connectors", list)
        self._segmentors: list[str] = self._get_config_or_raise("segmentors", list)
        self._validate_connectors_segmentors()

        self._allowed_terms: list[str] = self._get_config_or_raise("allowed_terms", list)
        self._hhmmss_delimiters: list[str] = self._get_config_or_raise("hhmmss_delimiters", list)
        self._decimal_delimiters: list[str] = self._get_config_or_raise("decimal_delimiters", list)
        self._thousand_delimiters: list[str] = self._get_config_or_raise("thousand_delimiters", list)
        self._fraction_delimiters: list[str] = self._get_config_or_raise("fraction_delimiters", list)
        self._validate_delimiters()

        self._scales_json = self._get_config_or_raise("scales", dict)
        self.millisecond: Scale
        self.second: Scale
        self.minute: Scale
        self.hour: Scale
        self.day: Scale
        self.week: Scale
        self.month: Scale
        self.year: Scale
        self.decade: Scale
        self.century: Scale
        self.scales: list[Scale] = []
        self._load_scales(self._scales_json)
        self._validate_scales()

        self._numerals_json: dict[str, dict[str, Any]] = self._get_config_or_raise("numerals", dict)
        self.numerals: list[Numeral] = []
        self._load_numerals(self._numerals_json)

        self.extra_data: dict[str, Any] = self._get_config_or_raise("extra_data", dict)

    @property
    def parser(self) -> Callable[[str, Locale], ParsedTimeLength]:
        """Return the parser function attached to the Locale."""

        if self._parser and callable(self._parser):
            self._validate()
            return self._parser

        raise InvalidParserError(self)

    @property
    def connectors(self) -> list[str]:
        """Return the connectors if valid."""
        self._validate_connectors_segmentors()
        return self._connectors

    @connectors.setter
    def connectors(self, value: list[str]) -> None:
        self._connectors = value
        self._validate_connectors_segmentors()

    @property
    def segmentors(self) -> list[str]:
        """Return the segmentors if valid."""
        self._validate_connectors_segmentors()
        return self._segmentors

    @segmentors.setter
    def segmentors(self, value: list[str]) -> None:
        self._segmentors = value
        self._validate_connectors_segmentors()

    @property
    def allowed_terms(self) -> list[str]:
        """Return the allowed terms."""
        return self._allowed_terms

    @allowed_terms.setter
    def allowed_terms(self, value: list[str]) -> None:
        self._allowed_terms = value

    @property
    def decimal_delimiters(self) -> list[str]:
        """Return the decimal delimiters if valid."""
        self._validate_delimiters()
        return self._decimal_delimiters

    @decimal_delimiters.setter
    def decimal_delimiters(self, value: list[str]) -> None:
        self._decimal_delimiters = value
        self._validate_delimiters()

    @property
    def thousand_delimiters(self) -> list[str]:
        """Return the thousand delimiters if valid."""
        self._validate_delimiters()
        return self._thousand_delimiters

    @thousand_delimiters.setter
    def thousand_delimiters(self, value: list[str]) -> None:
        self._thousand_delimiters = value
        self._validate_delimiters()

    @property
    def hhmmss_delimiters(self) -> list[str]:
        """Return the hhmmss delimiters if valid."""
        self._validate_delimiters()
        return self._hhmmss_delimiters

    @hhmmss_delimiters.setter
    def hhmmss_delimiters(self, value: list[str]) -> None:
        self._hhmmss_delimiters = value
        self._validate_delimiters()

    @property
    def fraction_delimiters(self) -> list[str]:
        """Return the fraction delimiters if valid."""
        self._validate_delimiters()
        return self._fraction_delimiters

    @fraction_delimiters.setter
    def fraction_delimiters(self, value: list[str]) -> None:
        self._fraction_delimiters = value
        self._validate_delimiters()

    @property
    def delimiters(self) -> list[str]:
        """Return a list of all delimiters if valid."""
        self._validate_delimiters()
        return (
            self._hhmmss_delimiters + self._decimal_delimiters + self._thousand_delimiters + self._fraction_delimiters
        )

    @property
    def specials(self) -> list[str]:
        """Return a list of all special characters."""
        return self._connectors + self._segmentors + self._allowed_terms + self.delimiters

    @property
    def usable_scales(self) -> list[Scale]:
        """Return a list of usable scales."""
        return [scale for scale in self.scales if scale.valid and scale.enabled]

    @property
    def usable_numerals(self) -> list[Numeral]:
        """Return a list of usable numerals."""
        return [numeral for numeral in self.numerals if numeral.valid and numeral.enabled]

    @property
    def base_scale(self) -> Scale:
        """---
        Return the base `Scale` for `self`.

        #### Raises
        - `NoValidScalesError` when no valid and enabled scales are found.

        #### Returns
        - The base `Scale` for the locale. By default this is `Second`, but if it is not valid or enabled,
        the first valid and enabled scale will be used.
        """

        base = self.second if self.second.enabled and self.second.valid else None

        if not base:
            usable_scales = self.usable_scales
            base = usable_scales[0] if usable_scales else None

            if not base:
                raise NoValidScalesError

        return base

    def get_scale(self, term: str) -> Scale | None:
        """---
        Get a `Scale` from a term.

        #### Raises
        - `InvalidScaleError` when the scale is not valid.

        #### Returns
        - The `Scale` that contains the term in its terms list.
        - `None` if no scale contains the term.
        """

        for scale in self.scales:
            if term in scale.terms:
                if not scale.valid:
                    raise InvalidScaleError(scale.singular)
                return scale

        return None

    def get_numeral(self, term: str) -> Numeral | None:
        """---
        Get a `Numeral` from a term.

        #### Raises
        - `InvalidNumeralError` when the numeral is not valid.

        #### Returns
        - The `Numeral` that contains the term in its terms list.
        - `None` if no numeral contains the term.
        """

        for numeral in self.numerals:
            if term in numeral.terms:
                if not numeral.valid:
                    raise InvalidNumeralError(numeral.name)
                return numeral

        return None

    def _load_config(self, json_path: str) -> dict[str, Any]:
        if not os.path.exists(json_path) or not os.path.isfile(json_path):
            raise InvalidLocaleError(self, f"The provided config does not exist: {repr(json_path)}")

        with open(json_path, "r", encoding="utf-8") as f:
            config: dict[str, Any] = json.load(f)

        if not config:
            raise InvalidLocaleError(self, f"The provided config is empty: {repr(json_path)}")

        return config

    def _load_parser(self, base_dir: str) -> Callable[[str, Locale], ParsedTimeLength]:
        """Load the parser function from the parser file."""

        parser_path = os.path.join(base_dir, "parsers", self._parser_file)
        full_parser_path: str | None = (
            parser_path
            if os.path.exists(parser_path)
            else self._parser_file
            if os.path.exists(self._parser_file)
            else None
        )
        module_name, _ = os.path.splitext(os.path.basename(full_parser_path)) if full_parser_path else ("", "")

        try:
            if not full_parser_path:
                raise FileNotFoundError

            spec = util.spec_from_file_location(module_name, full_parser_path)

            if not spec or not hasattr(spec, "loader") or not spec.loader:
                raise FileNotFoundError

            module = util.module_from_spec(spec)
            spec.loader.exec_module(module)
            parser: Callable[[str, Locale], ParsedTimeLength] | None = getattr(module, module_name, None)

            if not parser:
                raise AttributeError
            else:
                return parser
        except (ModuleNotFoundError, FileNotFoundError) as e:
            raise InvalidLocaleError(self, f"Parser file not found: {repr(self._parser_file)}") from e
        except AttributeError as e:
            raise InvalidLocaleError(
                self, f"Parser function {repr(module_name)} not found in parser file: {repr(self._parser_file)}"
            ) from e

    def _load_flags(self, flags: FailureFlags | None) -> FailureFlags:
        """Load the flags from the config or the passed flags."""

        if flags is None:
            combined_flags = FailureFlags(0)

            for flag in self._get_config_or_raise("flags", list):
                try:
                    combined_flags |= FailureFlags[flag]
                except KeyError as e:
                    raise InvalidLocaleError(self, f"Invalid flag provided in config: {repr(flag)}") from e

            return combined_flags

        return flags

    def _load_settings(self, settings: ParserSettings | None) -> ParserSettings:
        """Load the settings from the config or the passed settings."""

        if settings is None:
            try:
                settings = ParserSettings(**self._get_config_or_raise("settings", dict))
            except TypeError as e:
                if "got an unexpected keyword argument" in str(e):
                    key: str = str(e).split("'")[1]
                    raise InvalidLocaleError(self, f"Invalid setting provided in config: {repr(key)}") from e
                else:
                    raise InvalidLocaleError(self, "Invalid settings provided in config.") from e

        return settings

    def _load_scales(self, scales_json: dict) -> None:
        """Load the scales from the config."""

        def process_scale(scale_json: dict, scale_name: str) -> None:
            if not scale_name:
                raise InvalidScaleError(scale_name, "A scale key is empty.")
            elif not all(key in scale_json for key in ["scale", "singular", "plural", "terms"]):
                raise InvalidScaleError(scale_name)
            else:
                try:
                    if isinstance(scale_json["scale"], str):
                        scale_json["scale"] = float(Fraction(scale_json["scale"]))

                    scale_json["terms"] = tuple(scale_json["terms"])
                    scale_obj: Scale = Scale(**scale_json)

                    setattr(self, scale_name, scale_obj)
                    self.scales.append(scale_obj)
                except (ValueError, TypeError) as e:
                    raise InvalidScaleError(scale_name, f"{repr(scale_name)} contains invalid values.") from e

        default_scales = [
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
        ]

        if any(scale_name not in scales_json for scale_name in default_scales):
            raise InvalidLocaleError(self, "Default scales are missing from the config.")

        for scale_name in default_scales:
            scale_json = scales_json.get(scale_name, {})
            process_scale(scale_json, scale_name)

        for scale_name in scales_json:
            if scale_name not in default_scales:
                process_scale(scales_json[scale_name], scale_name)

    def _load_numerals(self, numerals_json: dict) -> None:
        """Load the numerals from the config."""

        for numeral_name in numerals_json:
            if not numeral_name:
                raise InvalidNumeralError(numeral_name, "A numeral key is empty.")
            elif not all(key in numerals_json[numeral_name] for key in ["type", "value", "terms"]):
                raise InvalidNumeralError(numeral_name)

            raw_type: str = numerals_json[numeral_name]["type"]

            try:
                if not raw_type or not isinstance(raw_type, str):
                    raise ValueError

                numeral_type: NumeralType = NumeralType(raw_type)
            except ValueError as e:
                raise InvalidNumeralError(
                    numeral_name, f"An invalid NumeralType was provided for {repr(numeral_name)}."
                ) from e

            value: float = (
                float(Fraction(numerals_json[numeral_name]["value"]))
                if isinstance(numerals_json[numeral_name]["value"], str)
                else float(numerals_json[numeral_name]["value"])
            )
            terms: tuple[str, ...] = tuple(numerals_json[numeral_name]["terms"])
            self.numerals.append(Numeral(numeral_name, numeral_type, value, terms))

    def _get_config_or_raise(self, key: str, target_type: type) -> Any:
        """Retrieve a value of specified type from the config or raise `InvalidLocaleError` if the value is invalid."""

        value = self._config.get(key)

        if value is None:
            raise InvalidLocaleError(self, f"No {repr(key)} key found in config.")

        if not isinstance(value, target_type):
            raise InvalidLocaleError(self, f"{repr(key)} key in config is not of type {repr(target_type.__name__)}.")

        return value

    def _validate_connectors_segmentors(self) -> bool:
        """Validate the values for the connectors and segmentors."""

        if set(self._connectors).intersection(self._segmentors):
            raise InvalidLocaleError(self, "Connectors and segmentors may not have overlap.")

        return True

    def _validate_delimiters(self) -> bool:
        """Validate the values for the delimiters."""

        all_delimiters = (
            self._decimal_delimiters + self._thousand_delimiters + self._hhmmss_delimiters + self._fraction_delimiters
        )

        if len(all_delimiters) != len(set(all_delimiters)):
            raise InvalidLocaleError(self, "Delimiters may not have overlap.")

        return True

    def _validate_scales(self) -> bool:
        """Validate the values for the scales."""

        if not self.usable_scales:
            raise NoValidScalesError

        return True

    def _validate(self) -> bool:
        """Validate the values for config attributes."""

        self._validate_connectors_segmentors()
        self._validate_delimiters()
        self._validate_scales()

        return True

    def __str__(self) -> str:
        """Return the name of the locale."""
        return self.__class__.__name__

    def __repr__(self) -> str:
        """Return a string representation of the locale with attributes included."""
        return f"{self.__str__()}(config_location={json.dumps(self._config_location)}, flags={repr(self.flags)}, settings={repr(self.settings)})"


class English(Locale):
    """---
    Represents the `English` context used for parsing lengths of time.

    #### Attributes
    - flags: `FailureFlags | None = None` — The flags that will cause parsing to fail.
        - If not `None`, flags loaded from the config will be overwritten.
    - settings: `ParserSettings | None = None` — The settings for the parser.
        - If not `None`, settings loaded from the config will be overwritten.

    #### Properties
    - `parser` — Return the parser function attached to the Locale.
    - `connectors` — Return the connectors if valid.
    - `segmentors` — Return the segmentors if valid.
    - `allowed_terms` — Return the allowed terms.
    - `hhmmss_delimiters` — Return the hhmmss delimiters if valid.
    - `decimal_delimiters` — Return the decimal delimiters if valid.
    - `thousand_delimiters` — Return the thousand delimiters if valid.
    - `fraction_delimiters` — Return the fraction delimiters if valid.
    - `delimiters` — Return a list of all delimiters if valid.
    - `specials` — Return a list of all special characters.
    - `usable_scales` — Return a list of valid and enabled scales.
    - `usable_numerals` — Return a list of valid and enabled numerals.
    - `base_scale` — Return the base scale for the locale.

    #### Methods
    - `get_scale()` — Get the scale that contains a specific value in its terms list, if any.
    - `get_numeral()` — Get the numeral that contains a specific value in its terms list, if any.

    #### Raises
    - `InvalidLocaleError` when `english.json` does not exist or is malformed.
    - `InvalidParserError` when `self.parser` is not callable.
    - `NoValidScalesError` when no `Scale` is valid during validation.
    - `InvalidScaleError` when a `Scale` is invalid during initialization.
    - `InvalidNumeralError` when a `Numeral` is invalid during initialization.
    """

    def __init__(self, flags: FailureFlags | None = None, settings: ParserSettings | None = None) -> None:
        super().__init__("english.json", flags, settings)

    def __repr__(self) -> str:
        """Return a string representation of the locale with attributes included."""
        return f"English(flags={repr(self.flags)}, settings={repr(self.settings)})"


class Spanish(Locale):
    """---
    Represents the `Spanish` context used for parsing lengths of time.

    #### Attributes
    - flags: `FailureFlags | None = None` — The flags that will cause parsing to fail.
        - If not `None`, flags loaded from the config will be overwritten.
    - settings: `ParserSettings | None = None` — The settings for the parser.
        - If not `None`, settings loaded from the config will be overwritten.

    #### Properties
    - `parser` — Return the parser function attached to the Locale.
    - `connectors` — Return the connectors if valid.
    - `segmentors` — Return the segmentors if valid.
    - `allowed_terms` — Return the allowed terms.
    - `hhmmss_delimiters` — Return the hhmmss delimiters if valid.
    - `decimal_delimiters` — Return the decimal delimiters if valid.
    - `thousand_delimiters` — Return the thousand delimiters if valid.
    - `fraction_delimiters` — Return the fraction delimiters if valid.
    - `delimiters` — Return a list of all delimiters if valid.
    - `specials` — Return a list of all special characters.
    - `usable_scales` — Return a list of valid and enabled scales.
    - `usable_numerals` — Return a list of valid and enabled numerals.
    - `base_scale` — Return the base scale for the locale.

    #### Methods
    - `get_scale()` — Get the scale that contains a specific value in its terms list, if any.
    - `get_numeral()` — Get the numeral that contains a specific value in its terms list, if any.

    #### Raises
    - `InvalidLocaleError` when `spanish.json` does not exist or is malformed.
    - `InvalidParserError` when `self.parser` is not callable.
    - `NoValidScalesError` when no `Scale` is valid during validation.
    - `InvalidScaleError` when a `Scale` is invalid during initialization.
    - `InvalidNumeralError` when a `Numeral` is invalid during initialization.
    """

    def __init__(self, flags: FailureFlags | None = None, settings: ParserSettings | None = None) -> None:
        super().__init__("spanish.json", flags, settings)

    def __repr__(self) -> str:
        """Return a string representation of the locale with attributes included."""
        return f"Spanish(flags={repr(self.flags)}, settings={repr(self.settings)})"


class Guess:
    """---
    Represents an unknown `Locale` context used for parsing lengths of time.

    Does not contain any of the attributes of a `Locale`. Should never be used as a final
    `Locale`, but instead as an intermediary until a `Locale` is determined.

    #### Attributes
    - locales: `list[Locale]` — A list of all available `Locale` contexts.
        - Each `Locale` is automatically initialized with `self`.
        - Custom locales can be appended to this list. Access `self.flags` and `self.settings`
            to use the same flags and settings as the other locales.

    #### Properties
    - flags: `FailureFlags | None = None` — The flags that will cause parsing to fail.
        - If not `None`, flags loaded from the config will be overwritten.
        - Will be passed to each `Locale` in `self.locales` during initialization.
        - Access each `Locale` in `self.locales` to set individually customized flags,
            or to update the flags post-initialization.
    - settings: `ParserSettings | None = None` — The settings for the parser.
        - If not `None`, settings loaded from the config will be overwritten.
        - Will be passed to each `Locale` in `self.locales` during initialization.
        - Access each `Locale` in `self.locales` to set individually customized settings,
            or to update the settings post-initialization.

    #### Raises
    - `InvalidLocaleError` if any of the `Locale` configs are malformed or missing.
    """

    def __init__(
        self,
        flags: FailureFlags | None = None,
        settings: ParserSettings | None = None,
    ) -> None:
        self._flags: FailureFlags | None = flags
        self._settings: ParserSettings | None = settings
        self.locales: list[Locale] = [
            English(flags=flags, settings=settings),
            Spanish(flags=flags, settings=settings),
        ]

    @property
    def flags(self) -> FailureFlags | None:
        """Return the flags for the Guess."""
        return self._flags

    @property
    def settings(self) -> ParserSettings | None:
        """Return the settings for the Guess."""
        return self._settings

    def __str__(self) -> str:
        """Return the name of self."""
        return self.__class__.__name__

    def __repr__(self) -> str:
        """Return a string representation of the Guess with attributes included."""
        return f"Guess(flags={f'{repr(self.flags)}' if self.flags else None}, settings={repr(self.settings) if self.settings else None})"
