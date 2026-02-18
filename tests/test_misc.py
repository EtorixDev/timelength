# type: ignore

from datetime import datetime, timedelta, timezone
from typing import Callable, cast

import pytest
from timelength import English, FailureFlags, Guess, Locale, Numeral, ParserSettings, Scale, Spanish, TimeLength
from timelength.dataclasses import Buffer
from timelength.enums import NumeralType
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


@pytest.fixture
def tl_notstrict():
    return TimeLength(content="0 seconds", locale=English())


def test_parsedtimelength_reset(tl_notstrict: TimeLength):
    tl_notstrict.content = "5 seconds"
    tl_notstrict.parse()
    first_seconds = tl_notstrict.result.seconds
    tl_notstrict.content = "7 seconds"
    tl_notstrict.parse()
    second_seconds = tl_notstrict.result.seconds
    assert first_seconds != second_seconds


def test_parsedtimelength_delta(tl_notstrict: TimeLength):
    tl_notstrict.content = "5 seconds"
    tl_notstrict.parse()
    assert tl_notstrict.result.delta is not None
    assert tl_notstrict.result.delta.total_seconds() == 5


def test_parsedtimelength_strings(tl_notstrict: TimeLength):
    tl_notstrict.content = "5 seconds"
    tl_notstrict.parse()
    assert str(tl_notstrict.result) == "Success"
    assert repr(tl_notstrict.result) == 'ParsedTimeLength(success=True, seconds=5.0, invalid=(), valid=((5.0, Scale(scale=1.0, singular="second", plural="seconds", terms=("s", "S", "sec", "Sec", "SEC", "secs", "Secs", "SECS", "second", "Second", "SECOND", "seconds", "Seconds", "SECONDS"), enabled=True))))'
    tl_notstrict.content = "5 miles"
    tl_notstrict.parse()
    assert str(tl_notstrict.result) == "Failure"
    assert repr(tl_notstrict.result) == 'ParsedTimeLength(success=False, seconds=0.0, invalid=((5.0, FailureFlags.LONELY_VALUE), ("miles", FailureFlags.UNKNOWN_TERM)), valid=())'


def test_parsedtimelength_oob(tl_notstrict: TimeLength):
    tl_notstrict.content = "99999999999 trillion centuries"
    tl_notstrict.parse()
    assert tl_notstrict.result.success is True
    assert tl_notstrict.result.seconds == 3.153599999968464e32
    assert tl_notstrict.result.delta is None
    with pytest.raises(ParsedTimeDeltaError):
        tl_notstrict.ago()
    tl_notstrict.content = "9999 years"
    tl_notstrict.parse()
    with pytest.raises(PotentialDateTimeError):
        tl_notstrict.hence()


def test_scale():
    empty_scale = Scale()
    named_empty_scale = Scale(singular="second", plural="seconds")
    full_scale = Scale(scale=1, singular="second", plural="seconds", terms=("s", "sec", "secs"))
    assert empty_scale.valid is False and named_empty_scale.valid is False and full_scale.valid is True
    assert str(full_scale) == "Second"
    assert repr(full_scale) == 'Scale(scale=1, singular="second", plural="seconds", terms=("s", "sec", "secs"), enabled=True)'
    assert full_scale == Scale(scale=1)
    assert full_scale != Scale(scale=2)
    assert full_scale != Numeral(value=1)
    scales = {empty_scale: empty_scale, named_empty_scale: named_empty_scale, full_scale: full_scale}
    assert scales[empty_scale] == empty_scale


def test_numeral():
    empty_numeral = Numeral()
    named_empty_numeral = Numeral(name="one")
    full_numeral = Numeral(name="one", type=NumeralType.DIGIT, value=1, terms=("one",))
    assert empty_numeral.valid is False and named_empty_numeral.valid is False and full_numeral.valid is True
    assert str(full_numeral) == "One"
    assert repr(full_numeral) == 'Numeral(name="one", type=NumeralType.DIGIT, value=1, terms=("one"), enabled=True)'
    assert full_numeral == Numeral(value=1)
    assert full_numeral != Numeral(value=2)
    assert full_numeral != Scale(scale=1)
    numerals = {empty_numeral: empty_numeral, named_empty_numeral: named_empty_numeral, full_numeral: full_numeral}
    assert numerals[empty_numeral] == empty_numeral


def test_buffer():
    buffer = Buffer("5 minutes")
    assert buffer.value == "5 minutes"
    assert str(buffer) == "5 minutes"
    assert repr(buffer) == 'Buffer(value="5 minutes")'


def test_failureflags():
    assert str(FailureFlags.CONSECUTIVE_CONNECTOR | FailureFlags.MALFORMED_CONTENT) == "MALFORMED_CONTENT | CONSECUTIVE_CONNECTOR"
    assert repr(FailureFlags.CONSECUTIVE_CONNECTOR | FailureFlags.MALFORMED_CONTENT) == "(FailureFlags.MALFORMED_CONTENT | FailureFlags.CONSECUTIVE_CONNECTOR)"
    assert str(FailureFlags.MALFORMED_CONTENT) == "MALFORMED_CONTENT"
    assert repr(FailureFlags.MALFORMED_CONTENT) == "FailureFlags.MALFORMED_CONTENT"
    assert str(FailureFlags.NONE) == "NONE"
    assert repr(FailureFlags.NONE) == "FailureFlags.NONE"


def test_parser_settings():
    settings_default = ParserSettings()
    settings_custom = ParserSettings(allow_decimals_lacking_digits=False)
    assert str(settings_default) == "Default"
    assert str(settings_custom) == "Modified"
    assert repr(settings_default) == 'ParserSettings(assume_scale="SINGLE", limit_allowed_terms=True, allow_duplicate_scales=True, allow_thousands_extra_digits=False, allow_thousands_lacking_digits=False, allow_decimals_lacking_digits=True)'
    assert repr(settings_custom) == 'ParserSettings(assume_scale="SINGLE", limit_allowed_terms=True, allow_duplicate_scales=True, allow_thousands_extra_digits=False, allow_thousands_lacking_digits=False, allow_decimals_lacking_digits=False)'


def test_error_messages():
    assert str(PotentialDateTimeError()) == "The parsed value exceeds the bounds supported by datetime."
    assert str(PotentialDateTimeError("Testing error.")) == "Testing error."
    assert str(ParsedTimeDeltaError()) == "The parsed value exceeds the bounds supported by timedelta."
    assert str(ParsedTimeDeltaError("Testing error.")) == "Testing error."
    assert str(PotentialTimeDeltaError()) == "The parsed value exceeds the bounds supported by timedelta."
    assert str(PotentialTimeDeltaError("Testing error.")) == "Testing error."
    assert str(InvalidScaleError()) == "A scale is missing required attributes."
    assert str(InvalidScaleError("Test Scale")) == '"Test Scale" is missing required attributes.'
    assert str(InvalidScaleError("Test Scale", "Testing error.")) == "Testing error."
    assert str(NoValidScalesError()) == "No valid and enabled scales found."
    assert str(NoValidScalesError("Testing error.")) == "Testing error."
    assert str(InvalidNumeralError()) == "A numeral is missing required attributes."
    assert str(InvalidNumeralError("Test Numeral")) == '"Test Numeral" is missing required attributes.'
    assert str(InvalidNumeralError("Test Numeral", "Testing error.")) == "Testing error."
    assert str(NotALocaleError(buf := Buffer())) == f'"{type(buf).__name__}" is not an instance of Locale or Guess.'
    assert str(NotALocaleError(Buffer(), "Testing error.")) == "Testing error."
    assert str(InvalidLocaleError(loc := English())) == f"The configuration for {repr(str(loc))} is invalid."
    assert str(InvalidLocaleError(loc, "Testing error.")) == "Testing error."
    assert str(InvalidParserError(loc)) == f"{repr(str(loc))} is missing a valid parser function."
    assert str(InvalidParserError(loc, "Testing error.")) == "Testing error."


def test_locale_symbols():
    locale = English()
    locale._parser = cast(Callable, None)
    connectors = locale.connectors
    decimal_delimiters = locale.decimal_delimiters
    thousand_delimiters = locale.thousand_delimiters
    hhmmss_delimiters = locale.hhmmss_delimiters

    locale.allowed_terms = []
    assert locale.allowed_terms == []

    with pytest.raises(InvalidParserError):
        locale.parser

    with pytest.raises(InvalidLocaleError):
        locale.connectors = locale.segmentors

    locale.connectors = connectors

    with pytest.raises(InvalidLocaleError):
        locale.segmentors = locale.connectors

    with pytest.raises(InvalidLocaleError):
        locale.decimal_delimiters = locale.thousand_delimiters

    locale.decimal_delimiters = decimal_delimiters

    with pytest.raises(InvalidLocaleError):
        locale.thousand_delimiters = locale.decimal_delimiters

    locale.thousand_delimiters = thousand_delimiters

    with pytest.raises(InvalidLocaleError):
        locale.hhmmss_delimiters = locale.decimal_delimiters

    locale.hhmmss_delimiters = hhmmss_delimiters

    with pytest.raises(InvalidLocaleError):
        locale.fraction_delimiters = locale.decimal_delimiters


def test_locale_properties_functions():
    locale = English()
    scales = locale.scales

    with pytest.raises(NoValidScalesError):
        locale.scales = []
        locale.second.enabled = False
        locale.base_scale

    locale.second.enabled = True
    locale.scales = scales

    with pytest.raises(InvalidScaleError):
        locale.second.scale = 0
        locale.get_scale("second")

    locale.second.scale = 1
    assert locale.get_scale("fakeword") is None
    assert locale.get_scale("second") == locale.second

    one_numeral = locale.get_numeral("one")
    assert isinstance(one_numeral, Numeral)

    with pytest.raises(InvalidNumeralError):
        one_numeral.name = ""
        locale.get_numeral("one")

    one_numeral.name = "one"
    assert locale.get_numeral("fakeword") is None


def test_load_config(mocker):
    with pytest.raises(InvalidLocaleError):
        Locale("")

    with pytest.raises(InvalidLocaleError):
        mocker.patch("builtins.open", mocker.mock_open(read_data="{}"))
        Locale("english.json")


def test_load_parser(mocker):
    with pytest.raises(InvalidLocaleError) as excinfo1:
        mocker.patch("_frozen_importlib_external.SourceFileLoader.exec_module", return_value=None)
        Locale("english.json")

    assert isinstance(excinfo1.value.__cause__, AttributeError)

    with pytest.raises(InvalidLocaleError) as excinfo2:
        mocker.patch("importlib.util.spec_from_file_location", return_value=None)
        Locale("english.json")

    assert isinstance(excinfo2.value.__cause__, FileNotFoundError)

    with pytest.raises(InvalidLocaleError) as excinfo3:
        mocker.patch("importlib.util.spec_from_file_location", return_value=object())
        Locale("english.json")

    assert isinstance(excinfo3.value.__cause__, FileNotFoundError)

    class PlaceholderSpec:
        def __init__(self):
            self.loader = None

    with pytest.raises(InvalidLocaleError) as excinfo4:
        mocker.patch("importlib.util.spec_from_file_location", return_value=PlaceholderSpec())
        Locale("english.json")

    assert isinstance(excinfo4.value.__cause__, FileNotFoundError)

    with pytest.raises(InvalidLocaleError) as excinfo5:
        mocker.patch("builtins.open", mocker.mock_open(read_data='{"parser_file": "parser_fake.py"}'))
        Locale("english.json")

    assert isinstance(excinfo5.value.__cause__, FileNotFoundError)


def test_load_flags(mocker):
    eng = Locale("english.json")

    with pytest.raises(InvalidLocaleError) as excinfo1:
        mocker.patch("timelength.locales.Locale._get_config_or_raise", return_value=["FakeFlag"])
        eng._load_flags(None)

    assert isinstance(excinfo1.value.__cause__, KeyError)


def test_load_settings(mocker):
    eng = Locale("english.json")

    with pytest.raises(InvalidLocaleError) as excinfo1:
        mocker.patch("timelength.locales.Locale._get_config_or_raise", return_value={"FakeSetting": "FakeValue"})
        eng._load_settings(None)

    assert isinstance(excinfo1.value.__cause__, TypeError)
    assert "got an unexpected keyword argument" in str(excinfo1.value.__cause__)

    with pytest.raises(InvalidLocaleError) as excinfo2:
        mocker.patch("timelength.locales.Locale._get_config_or_raise", return_value=[])
        eng._load_settings(None)

    assert isinstance(excinfo2.value.__cause__, TypeError)
    assert "got an unexpected keyword argument" not in str(excinfo2.value.__cause__)


def test_load_scales():
    eng = Locale("english.json")

    empty_scale_data = {}

    with pytest.raises(InvalidLocaleError) as excinfo1:
        eng._load_scales(empty_scale_data)

    assert str(excinfo1.value) == "Default scales are missing from the config."

    custom_scale_data = {"fortnight": {"scale": 1209600, "singular": "fortnight", "plural": "fortnights", "terms": ["fortnight", "fortnights"]}}

    eng._load_scales({**eng._scales_json, **custom_scale_data})
    assert hasattr(eng, "fortnight")

    no_name_data = {"": {"scale": 1, "singular": "second", "plural": "seconds", "terms": ["s", "sec", "secs"]}}

    with pytest.raises(InvalidScaleError) as excinfo2:
        eng._load_scales({**eng._scales_json, **no_name_data})

    assert str(excinfo2.value) == "A scale key is empty."

    not_enough_data = {"notenough": {"scale": 1, "singular": "second", "plural": "seconds"}}

    with pytest.raises(InvalidScaleError) as excinfo3:
        eng._load_scales({**eng._scales_json, **not_enough_data})

    assert str(excinfo3.value) == '"notenough" is missing required attributes.'

    invalid_value_data = {"invalid": {"scale": "one", "singular": "invalid", "plural": "invalids", "terms": ["invalid", "invalids"]}}

    with pytest.raises(InvalidScaleError) as excinfo4:
        eng._load_scales({**eng._scales_json, **invalid_value_data})

    assert isinstance(excinfo4.value.__cause__, ValueError)

    invalid_type_data = {"invalid": {"scale": 1, "singular": "invalid", "plural": "invalids", "terms": 1}}

    with pytest.raises(InvalidScaleError) as excinfo5:
        eng._load_scales({**eng._scales_json, **invalid_type_data})

    assert isinstance(excinfo5.value.__cause__, TypeError)

    too_many_keys_data = {"toomany": {"scale": 1, "singular": "second", "plural": "seconds", "terms": ["s", "sec", "secs"], "fake_key": "fake"}}

    with pytest.raises(InvalidScaleError) as excinfo6:
        eng._load_scales({**eng._scales_json, **too_many_keys_data})

    assert isinstance(excinfo6.value.__cause__, TypeError)

    eng.scales = []

    with pytest.raises(NoValidScalesError):
        eng._validate_scales()


def test_load_numerals():
    eng = Locale("english.json")

    no_name_data = {"": {"type": "DIGIT", "value": 1, "terms": ["one"]}}

    with pytest.raises(InvalidNumeralError) as excinfo1:
        eng._load_numerals(no_name_data)

    assert str(excinfo1.value) == "A numeral key is empty."

    not_enough_data = {"notenough": {"type": "DIGIT", "value": 1}}

    with pytest.raises(InvalidNumeralError) as excinfo2:
        eng._load_numerals(not_enough_data)

    assert str(excinfo2.value) == '"notenough" is missing required attributes.'

    invalid_value_data = {"invalid": {"type": ["INVALID"], "value": 1, "terms": ["invalid"]}}

    with pytest.raises(InvalidNumeralError) as excinfo3:
        eng._load_numerals(invalid_value_data)

    assert isinstance(excinfo3.value.__cause__, ValueError)


def test_get_config_or_raise():
    eng = Locale("english.json")
    eng._config = {"connectors": 1}

    with pytest.raises(InvalidLocaleError) as excinfo1:
        eng._get_config_or_raise("connectors", list)

    assert str(excinfo1.value) == "'connectors' key in config is not of type 'list'."

    with pytest.raises(InvalidLocaleError) as excinfo2:
        eng._get_config_or_raise("fake_key", list)

    assert str(excinfo2.value) == "No 'fake_key' key found in config."


def test_locale_str_repr():
    loc = Locale("english.json")
    assert str(loc) == "Locale"
    assert repr(loc) == 'Locale(config_location="english.json", flags=FailureFlags.NONE, settings=ParserSettings(assume_scale="SINGLE", limit_allowed_terms=True, allow_duplicate_scales=True, allow_thousands_extra_digits=False, allow_thousands_lacking_digits=False, allow_decimals_lacking_digits=True))'

    eng = English()
    assert str(eng) == "English"
    assert repr(eng) == 'English(flags=FailureFlags.NONE, settings=ParserSettings(assume_scale="SINGLE", limit_allowed_terms=True, allow_duplicate_scales=True, allow_thousands_extra_digits=False, allow_thousands_lacking_digits=False, allow_decimals_lacking_digits=True))'

    spa = Spanish()
    assert str(spa) == "Spanish"
    assert repr(spa) == 'Spanish(flags=FailureFlags.NONE, settings=ParserSettings(assume_scale="SINGLE", limit_allowed_terms=True, allow_duplicate_scales=True, allow_thousands_extra_digits=False, allow_thousands_lacking_digits=False, allow_decimals_lacking_digits=True))'

    guess = Guess()
    assert str(guess) == "Guess"
    assert repr(guess) == "Guess(flags=None, settings=None)"

    guess_none_flag = Guess(flags=FailureFlags.NONE)
    assert repr(guess_none_flag) == "Guess(flags=FailureFlags.NONE, settings=None)"


def test_timelength():
    with pytest.raises(NotALocaleError):
        tl = TimeLength(content="5 seconds", locale=cast(Locale, Buffer()))

    tl = TimeLength(content="3 days, 2 hours, 1 minute, 30.5 seconds", locale=English())
    assert str(tl) == "3 Days, 02:01:30.5"
    assert tl._convert_to_hhmmss(tl.result.seconds) == "3 Days, 02:01:30.5"

    tl.content = "5 minutos"
    tl.parse(guess_locale=True)
    assert isinstance(tl.locale, Spanish)
    assert tl._convert_to_hhmmss(tl.result.seconds) == "00:05:00"
    assert repr(tl) == 'TimeLength(content="5 minutos", locale=Spanish(flags=FailureFlags.NONE, settings=ParserSettings(assume_scale="SINGLE", limit_allowed_terms=True, allow_duplicate_scales=True, allow_thousands_extra_digits=False, allow_thousands_lacking_digits=False, allow_decimals_lacking_digits=True)))'

    # Matches both English and Spanish
    tl.content = "5 min"
    tl.parse(guess_locale=True)
    assert isinstance(tl.locale, English)

    tl.content = "5 minutes"
    tl.parse(guess_locale=True)
    assert isinstance(tl.locale, English)


def test_timelength_conversions():
    tl = TimeLength(content="5 minutes", locale=English())
    base = datetime.now(tz=timezone.utc)
    assert tl.ago(base=base) == (base - timedelta(minutes=5))
    assert tl.hence(base=base) == (base + timedelta(minutes=5))

    tl.content = "999,999 centuries"
    tl.parse()

    with pytest.raises(ParsedTimeDeltaError):
        tl.ago()

    with pytest.raises(ParsedTimeDeltaError):
        tl.hence()

    tl.content = tl._convert_to_hhmmss(datetime(9999, 12, 31, 23, 59, 59, 999999, tzinfo=timezone.utc).timestamp())
    tl.parse()

    with pytest.raises(PotentialDateTimeError):
        tl.ago()

    with pytest.raises(PotentialDateTimeError):
        tl.hence()

    tl = TimeLength(content="1 Century", locale=English())
    assert tl.to_milliseconds() == 3153600000 * 1000
    assert tl.to_minutes() == 3153600000 / 60
    assert tl.to_hours() == 3153600000 / 60 / 60
    assert tl.to_days() == 3153600000 / 60 / 60 / 24
    assert tl.to_weeks() == 3153600000 / 60 / 60 / 24 / 7
    assert tl.to_months() == 3153600000 / 60 / 60 / 24 / 30.5
    assert tl.to_years() == 3153600000 / 60 / 60 / 24 / 365
    assert tl.to_decades() == 3153600000 / 60 / 60 / 24 / 365 / 10
    assert tl.to_centuries() == 1

    tl_precise = TimeLength(content="90 seconds", locale=English())
    assert tl_precise.to_minutes() == 1.5
    assert tl_precise.to_minutes(max_precision=0) == 2.0

    tl.locale.minute.scale = 0

    with pytest.raises(InvalidScaleError):
        tl.to_minutes()


def test_timelength_dunder_methods():
    tl_fail = TimeLength(content="abcd", locale=English())
    tl_zero = TimeLength(content="0 seconds", locale=English())
    tl_5_seconds = TimeLength(content="5 seconds", locale=English())
    tl_5_minutes = TimeLength(content="5 minutes", locale=English())
    tl_10_seconds = TimeLength(content="10 seconds", locale=English())
    tl_10_minutes = TimeLength(content="10 minutes", locale=English())
    td_5_seconds = timedelta(seconds=5)
    td_5_minutes = timedelta(minutes=5)
    td_10_seconds = timedelta(seconds=10)
    td_10_minutes = timedelta(minutes=10)
    td_zero = timedelta(seconds=0)
    dt_now = datetime.now(tz=timezone.utc)
    seven = 7
    hundred = 100
    buffer = Buffer()

    # Left Addition
    assert isinstance((res := tl_5_minutes + tl_10_minutes), TimeLength) and res.result.seconds == 300 + 600
    assert isinstance((res := tl_5_minutes + td_10_minutes), TimeLength) and res.result.seconds == 300 + 600
    assert isinstance((res := tl_5_minutes + hundred), TimeLength) and res.result.seconds == 300 + 100
    assert tl_5_minutes.__add__(buffer) is NotImplemented
    assert tl_5_minutes.__add__(dt_now) is NotImplemented

    for unsupported in (buffer, dt_now):
        with pytest.raises(TypeError):
            _ = tl_5_minutes + unsupported

    # Right Addition
    assert isinstance((res := dt_now + tl_5_minutes), datetime) and (res - dt_now).total_seconds() == 300
    assert isinstance((res := td_5_minutes + tl_5_minutes), timedelta) and res.total_seconds() == 300 + 300
    assert tl_5_minutes.__radd__(buffer) is NotImplemented
    assert tl_5_minutes.__radd__(hundred) is NotImplemented

    for unsupported in (buffer, hundred):
        with pytest.raises(TypeError):
            _ = unsupported + tl_5_minutes

    # Left Subtraction
    assert isinstance((res := tl_5_minutes - tl_10_minutes), TimeLength) and res.result.seconds == abs(300 - 600)
    assert isinstance((res := tl_5_minutes - td_10_minutes), TimeLength) and res.result.seconds == abs(300 - 600)
    assert isinstance((res := tl_5_minutes - hundred), TimeLength) and res.result.seconds == abs(300 - 100)
    assert tl_5_minutes.__sub__(buffer) is NotImplemented
    assert tl_5_minutes.__sub__(dt_now) is NotImplemented

    for unsupported in (buffer, dt_now):
        with pytest.raises(TypeError):
            _ = tl_5_minutes - unsupported

    # Right Subtraction
    assert isinstance((res := dt_now - tl_5_minutes), datetime) and (res - dt_now).total_seconds() == -300
    assert isinstance((res := td_5_minutes - tl_5_minutes), timedelta) and res.total_seconds() == 300 - 300
    assert tl_5_minutes.__rsub__(buffer) is NotImplemented
    assert tl_5_minutes.__rsub__(hundred) is NotImplemented

    for unsupported in (buffer, hundred):
        with pytest.raises(TypeError):
            _ = unsupported - tl_5_minutes

    # Multiplication
    assert isinstance((res := tl_5_minutes * -hundred), TimeLength) and res.result.seconds == abs(300 * -100)
    assert isinstance((res := -hundred * tl_5_minutes), TimeLength) and res.result.seconds == abs(-100 * 300)
    assert tl_5_minutes.__mul__(buffer) is NotImplemented
    assert tl_5_minutes.__mul__(dt_now) is NotImplemented
    assert tl_5_minutes.__mul__(tl_10_minutes) is NotImplemented
    assert tl_5_minutes.__mul__(td_10_minutes) is NotImplemented

    for unsupported in (buffer, dt_now, tl_10_minutes, td_10_minutes):
        with pytest.raises(TypeError):
            _ = tl_5_minutes * unsupported

    # Left True Division
    assert isinstance((res := tl_5_minutes / tl_10_minutes), float) and res == 300 / 600
    assert isinstance((res := tl_5_minutes / td_10_minutes), float) and res == 300 / 600
    assert isinstance((res := tl_5_minutes / hundred), TimeLength) and res.result.seconds == 300 / 100
    assert tl_5_minutes.__truediv__(buffer) is NotImplemented
    assert tl_5_minutes.__truediv__(dt_now) is NotImplemented

    for unsupported in (buffer, dt_now):
        with pytest.raises(TypeError):
            _ = tl_5_minutes / unsupported

    with pytest.raises(ZeroDivisionError):
        _ = tl_5_minutes / tl_zero

    with pytest.raises(ZeroDivisionError):
        _ = tl_5_minutes / td_zero

    with pytest.raises(ZeroDivisionError):
        _ = tl_5_minutes / 0

    # Right True Division
    assert isinstance((res := td_10_minutes / tl_5_minutes), float) and res == 600 / 300
    assert tl_5_minutes.__rtruediv__(buffer) is NotImplemented
    assert tl_5_minutes.__rtruediv__(hundred) is NotImplemented
    assert tl_5_minutes.__rtruediv__(dt_now) is NotImplemented

    for unsupported in (buffer, hundred, dt_now):
        with pytest.raises(TypeError):
            _ = unsupported / tl_5_minutes

    with pytest.raises(ZeroDivisionError):
        _ = td_10_minutes / tl_zero

    # Left Floor Division
    assert isinstance((res := tl_5_minutes // tl_10_minutes), int) and res == 300 // 600
    assert isinstance((res := tl_5_minutes // td_10_minutes), int) and res == 300 // 600
    assert isinstance((res := tl_5_minutes // hundred), TimeLength) and res.result.seconds == 300 // 100
    assert tl_5_minutes.__floordiv__(buffer) is NotImplemented
    assert tl_5_minutes.__floordiv__(dt_now) is NotImplemented

    for unsupported in (buffer, dt_now):
        with pytest.raises(TypeError):
            _ = tl_5_minutes // unsupported

    with pytest.raises(ZeroDivisionError):
        _ = tl_5_minutes // tl_zero

    with pytest.raises(ZeroDivisionError):
        _ = tl_5_minutes // td_zero

    with pytest.raises(ZeroDivisionError):
        _ = tl_5_minutes // 0

    # Right Floor Division
    assert isinstance((res := td_10_minutes // tl_5_minutes), int) and res == 600 // 300
    assert tl_5_minutes.__rfloordiv__(buffer) is NotImplemented
    assert tl_5_minutes.__rfloordiv__(hundred) is NotImplemented
    assert tl_5_minutes.__rfloordiv__(dt_now) is NotImplemented

    for unsupported in (buffer, hundred, dt_now):
        with pytest.raises(TypeError):
            _ = unsupported // tl_5_minutes

    with pytest.raises(ZeroDivisionError):
        _ = td_10_minutes // tl_zero

    # Left Modulus
    assert isinstance((res := tl_5_minutes % tl_10_minutes), TimeLength) and res.result.seconds == 300 % 600
    assert isinstance((res := tl_5_minutes % td_10_minutes), TimeLength) and res.result.seconds == 300 % 600
    assert isinstance((res := tl_5_minutes % hundred), TimeLength) and res.result.seconds == 300 % 100
    assert tl_5_minutes.__mod__(buffer) is NotImplemented
    assert tl_5_minutes.__mod__(dt_now) is NotImplemented

    for unsupported in (buffer, dt_now):
        with pytest.raises(TypeError):
            _ = tl_5_minutes % unsupported

    with pytest.raises(ZeroDivisionError):
        _ = tl_5_minutes % tl_zero

    with pytest.raises(ZeroDivisionError):
        _ = tl_5_minutes % td_zero

    with pytest.raises(ZeroDivisionError):
        _ = tl_5_minutes % 0

    # Right Modulus
    assert isinstance((res := td_10_minutes % tl_5_minutes), timedelta) and res.total_seconds() == 600 % 300
    assert tl_5_minutes.__rmod__(buffer) is NotImplemented
    assert tl_5_minutes.__rmod__(hundred) is NotImplemented
    assert tl_5_minutes.__rmod__(dt_now) is NotImplemented

    for unsupported in (buffer, hundred, dt_now):
        with pytest.raises(TypeError):
            _ = unsupported % tl_5_minutes

    with pytest.raises(ZeroDivisionError):
        _ = td_10_minutes % tl_zero

    # Left Divmod
    assert isinstance((res := divmod(tl_5_minutes, tl_10_minutes)), tuple) and len(res) == 2 and res[0] == 300 // 600 and isinstance(res[1], TimeLength) and res[1].result.seconds == 300 % 600
    assert isinstance((res := divmod(tl_5_minutes, td_10_minutes)), tuple) and len(res) == 2 and res[0] == 300 // 600 and isinstance(res[1], TimeLength) and res[1].result.seconds == 300 % 600
    assert isinstance((res := divmod(tl_5_minutes, hundred)), tuple) and len(res) == 2 and res[0] == 300 // 100 and isinstance(res[1], TimeLength) and res[1].result.seconds == 300 % 100
    assert tl_5_minutes.__divmod__(buffer) is NotImplemented
    assert tl_5_minutes.__divmod__(dt_now) is NotImplemented

    for unsupported in (buffer, dt_now):
        with pytest.raises(TypeError):
            _ = divmod(tl_5_minutes, unsupported)

    with pytest.raises(ZeroDivisionError):
        _ = divmod(tl_5_minutes, tl_zero)

    with pytest.raises(ZeroDivisionError):
        _ = divmod(tl_5_minutes, td_zero)

    with pytest.raises(ZeroDivisionError):
        _ = divmod(tl_5_minutes, 0)

    # Right Divmod
    assert isinstance((res := divmod(td_10_minutes, tl_5_minutes)), tuple) and len(res) == 2 and res[0] == 600 // 300 and isinstance(res[1], timedelta) and res[1].total_seconds() == 600 % 300
    assert tl_5_minutes.__rdivmod__(buffer) is NotImplemented
    assert tl_5_minutes.__rdivmod__(hundred) is NotImplemented
    assert tl_5_minutes.__rdivmod__(dt_now) is NotImplemented

    for unsupported in (buffer, hundred, dt_now):
        with pytest.raises(TypeError):
            _ = divmod(unsupported, tl_5_minutes)

    with pytest.raises(ZeroDivisionError):
        _ = divmod(td_10_minutes, tl_zero)

    # Left Power
    assert isinstance((res := tl_5_seconds**seven), TimeLength) and res.result.seconds == 5**7
    assert isinstance((res := pow(tl_5_seconds, seven, tl_10_seconds)), TimeLength) and res.result.seconds == pow(5, 7, 10)
    assert isinstance((res := pow(tl_5_seconds, seven, td_5_seconds)), TimeLength) and res.result.seconds == pow(5, 7, 5)
    assert isinstance((res := pow(tl_5_seconds, seven, seven)), TimeLength) and res.result.seconds == pow(5, 7, 7)
    assert tl_5_seconds.__pow__(buffer) is NotImplemented
    assert tl_5_seconds.__pow__(dt_now) is NotImplemented
    assert tl_5_seconds.__pow__(td_10_minutes) is NotImplemented
    assert tl_5_seconds.__pow__(tl_10_seconds) is NotImplemented

    for unsupported in (buffer, dt_now, td_10_minutes, tl_10_seconds):
        with pytest.raises(TypeError):
            _ = tl_5_seconds**unsupported

    with pytest.raises(ValueError):
        _ = pow(tl_5_seconds, seven, 0)

    with pytest.raises(ValueError):
        _ = pow(tl_5_seconds, seven, td_zero)

    with pytest.raises(ValueError):
        _ = pow(tl_5_seconds, seven, tl_zero)

    # Right Power
    # This method was excluded from the class rather than returning NotImplemented to
    # maintain consistency with invert which was forced to be excluded, as explained below.
    # assert tl_5_seconds.__rpow__(buffer) is NotImplemented
    # assert tl_5_seconds.__rpow__(hundred) is NotImplemented
    # assert tl_5_seconds.__rpow__(dt_now) is NotImplemented
    # assert tl_5_seconds.__rpow__(td_5_seconds) is NotImplemented
    # assert tl_5_seconds.__rpow__(tl_10_seconds) is NotImplemented

    for unsupported in (buffer, hundred, dt_now, td_5_seconds, tl_10_seconds):
        with pytest.raises(TypeError):
            _ = unsupported**tl_5_seconds

    # Comparisons & Unary
    assert bool(tl_5_seconds) is True
    assert bool(tl_zero) is True
    assert bool(tl_fail) is False

    assert len(tl_5_seconds) == len(tl_5_seconds.content)

    assert abs(tl_5_seconds) == tl_5_seconds
    assert +tl_5_seconds == tl_5_seconds
    assert -tl_5_seconds == tl_5_seconds

    # Python does not auto raise TypeError for NotImplemented returned by
    # unary operations, so this method was excluded from the class.
    # assert tl_5_seconds.__invert__() is NotImplemented

    with pytest.raises(TypeError):
        _ = ~tl_5_seconds

    assert tl_10_seconds > tl_5_seconds
    assert tl_10_seconds > td_5_seconds
    assert tl_10_seconds > 5

    assert tl_10_seconds.__gt__(buffer) is NotImplemented
    assert tl_10_seconds.__gt__(dt_now) is NotImplemented

    for unsupported in (buffer, dt_now):
        with pytest.raises(TypeError):
            _ = tl_10_seconds > unsupported

    assert tl_10_seconds >= tl_5_seconds
    assert tl_10_seconds >= tl_10_seconds
    assert tl_10_seconds >= td_5_seconds
    assert tl_10_seconds >= td_10_seconds
    assert tl_10_seconds >= 5
    assert tl_10_seconds >= 10

    assert tl_10_seconds.__ge__(buffer) is NotImplemented
    assert tl_10_seconds.__ge__(dt_now) is NotImplemented

    for unsupported in (buffer, dt_now):
        with pytest.raises(TypeError):
            _ = tl_10_seconds >= unsupported

    assert tl_5_seconds < tl_10_seconds
    assert tl_5_seconds < td_10_seconds
    assert tl_5_seconds < 10

    assert tl_5_seconds.__lt__(buffer) is NotImplemented
    assert tl_5_seconds.__lt__(dt_now) is NotImplemented

    for unsupported in (buffer, dt_now):
        with pytest.raises(TypeError):
            _ = tl_5_seconds < unsupported

    assert tl_5_seconds <= tl_10_seconds
    assert tl_5_seconds <= tl_5_seconds
    assert tl_5_seconds <= td_10_seconds
    assert tl_5_seconds <= td_5_seconds
    assert tl_5_seconds <= 10
    assert tl_5_seconds <= 5

    assert tl_5_seconds.__le__(buffer) is NotImplemented
    assert tl_5_seconds.__le__(dt_now) is NotImplemented

    for unsupported in (buffer, dt_now):
        with pytest.raises(TypeError):
            _ = tl_5_seconds <= unsupported

    assert tl_5_seconds == tl_5_seconds
    assert tl_5_seconds == td_5_seconds
    assert tl_5_seconds == 5

    assert tl_5_seconds.__eq__(buffer) is False
    assert tl_5_seconds.__eq__(dt_now) is False

    assert tl_5_seconds != tl_10_seconds
    assert tl_5_seconds != td_10_seconds
    assert tl_5_seconds != 10

    assert tl_5_seconds.__ne__(buffer) is True
    assert tl_5_seconds.__ne__(dt_now) is True
