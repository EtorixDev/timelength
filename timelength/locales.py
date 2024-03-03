from typing import Union
import importlib
import json
import os


from timelength.errors import LocaleConfigError
from timelength.dataclasses import Scale


class Locale:
    """
    Represents a default Locale, each of which may handle parsing differently.

    ### Attributes

    - `json_location` (`str`): The string path to the config file for this Locale.
    """

    def __init__(self, json_location: str = "locales/english.json"):
        """Initialize the `Locale` based on the passed config file."""
        self._json_location = json_location
        self._config = {}
        base_dir = os.path.dirname(__file__)

        if os.path.isabs(json_location):
            full_json_path = json_location
        elif "locales/" in json_location:
            full_json_path = os.path.join(base_dir, json_location)
        else:
            full_json_path = json_location

        self._load_config(full_json_path)

        if not self._config:
            raise LocaleConfigError("Provided config is empty.")

        self._parser_path: str = os.path.join(
            base_dir, "parsers", self._get_config_or_raise("parser_file")
        )
        self._parser = None
        self._load_parser(base_dir)

        self._connectors = self._get_config_or_raise("connectors")
        self._segmentors = self._get_config_or_raise("segmentors")
        if set(self._connectors).intersection(self._segmentors):
            raise LocaleConfigError(
                "Connectors and Segmentors may not have overlap in config."
            )

        # _allowed_symbols may appear ONCE in a row in the input while strict is enabled.
        self._allowed_symbols = self._get_config_or_raise("allowed_symbols")
        self._decimal_separators = self._get_config_or_raise("decimal_separators")
        self._thousand_separators = self._get_config_or_raise("thousand_separators")
        if set(self._decimal_separators).intersection(self._thousand_separators):
            raise LocaleConfigError(
                "Decimal separators and Thousand separators may not have overlap in config."
            )

        # Default Scales can be disabled by removing them from the config. In their place an empty Scale of
        # scale 0 will be added. This will cause its related TimeLength conversion method, such as `to_minutes`,
        # to error as dividing by 0 is not allowed. Parsing wise, it will be ignored as the terms list is empty.
        scales_json = self._get_config_or_raise("scales")
        self._millisecond = (
            Scale(**self._config["scales"]["millisecond"])
            if "millisecond" in scales_json
            else Scale()
        )
        self._second = (
            Scale(**self._config["scales"]["second"])
            if "second" in scales_json
            else Scale()
        )
        self._minute = (
            Scale(**self._config["scales"]["minute"])
            if "minute" in scales_json
            else Scale()
        )
        self._hour = (
            Scale(**self._config["scales"]["hour"])
            if "hour" in scales_json
            else Scale()
        )
        self._day = (
            Scale(**self._config["scales"]["day"]) if "day" in scales_json else Scale()
        )
        self._week = (
            Scale(**self._config["scales"]["week"])
            if "week" in scales_json
            else Scale()
        )
        self._month = (
            Scale(**self._config["scales"]["month"])
            if "month" in scales_json
            else Scale()
        )
        self._year = (
            Scale(**self._config["scales"]["year"])
            if "year" in scales_json
            else Scale()
        )
        self._decade = (
            Scale(**self._config["scales"]["decade"])
            if "decade" in scales_json
            else Scale()
        )
        self._century = (
            Scale(**self._config["scales"]["century"])
            if "century" in scales_json
            else Scale()
        )
        self._scales: list = [
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
                setattr(self, f"_{scale_name}", custom_scale)
                self._scales.append(custom_scale)

        self._numerals = self._get_config_or_raise("numerals")
        self._extra_data = self._get_config_or_raise("extra_data")

    def _get_scale(self, text: str) -> Scale:
        """Get the scale that contains a specific value in its terms list."""
        for scale in self._scales:
            scale: Scale
            if text in scale.terms:
                return scale
        return None

    def _get_numeral(self, text: str) -> dict:
        """Get a numeral that contains a specific value in its terms list."""
        numeral = {}
        for numeral in self._numerals:
            if text in self._numerals[numeral]["terms"]:
                return self._numerals[numeral]
        return None

    def _load_parser(self, base_dir):
        """Load the parser file linked in the config file into a method attached to the `Locale`."""
        if (
            self._parser
            and callable(self._parser)
            and self._parser_path.endswith(f"{self._parser.__name__ }.py")
        ):
            return  # Parser already loaded for this locale.
        if self._parser_path:
            package_dir = os.path.dirname(base_dir)
            relative_path = os.path.relpath(self._parser_path, package_dir)
            module_path = relative_path.replace("\\", ".").split(".py")[0]

            function_name = module_path.split(".")[-1]
            try:
                module = importlib.import_module(module_path)
                self._parser = getattr(module, function_name, None)
            except ModuleNotFoundError:
                self._parser = None
                raise LocaleConfigError(
                    f"File not found: {self._parser_path}"
                ) from None
            except AttributeError:
                self._parser = None
                raise LocaleConfigError(
                    f"Parser function not found: {function_name}"
                ) from None
        else:
            raise LocaleConfigError("No parser path provided in config.")

    def _load_config(self, file: str):
        """Load the config from the provided path."""
        with open(file, "r") as f:
            self._config = json.load(f)

    def _get_config_or_raise(self, key: str) -> Union[str, float, list, dict]:
        """Retrieve a value from the config or raise if the value is not found."""
        value = self._config.get(key)
        if value is None:
            raise LocaleConfigError(
                f'Provided config is malformed. No "{key}" key provided.'
            )
        return value

    def __str__(self):
        """Return the name of the `Locale`."""
        return f"<{self.__class__.__name__}>"

    def __repr__(self):
        """Return a string representation of the `Locale` with the config path included."""
        return f'Locale("{self._json_location}")'


class CustomLocale(Locale):
    """
    Represents a custom `Locale`.

    ### Attributes

    - `json_location` (`str`): The string path to the config file for this `Locale`.
    """

    def __init__(self, path_to_json: str):
        super().__init__(path_to_json)


class English(Locale):
    """
    Represents the `English` `Locale`.
    """

    def __init__(self):
        super().__init__("locales/english.json")
