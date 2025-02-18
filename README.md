# timelength
<!-- [![](https://img.shields.io/pypi/v/timelength.svg?style=flat-square&color=5677a6)](https://pypi.org/project/timelength/)
[![](https://img.shields.io/pypi/pyversions/timelength.svg?style=flat-square&color=5677a6)](https://pypi.org/project/timelength/) -->
[![](https://img.shields.io/pypi/dm/timelength.svg?style=flat-square&color=5677a6)](https://pypi.org/project/timelength/)
[![](https://img.shields.io/github/actions/workflow/status/EtorixDev/timelength/tests.yml?branch=3.0.0-dev&style=flat-square&color=51a851)](https://github.com/EtorixDev/timelength)
[![](https://img.shields.io/badge/coverage-100%25-41c241?style=flat-square&color=51a851)](https://github.com/EtorixDev/timelength)
[![](https://img.shields.io/pypi/l/timelength.svg?style=flat-square&color=51a851)](https://pypi.org/project/timelength/)

A flexible python duration parser designed for human readable lengths of time, including long form durations such as `1 day, 5 hours, and 30 seconds`, short form durations such as `1d5h30s`, numerals such as `twelve hours`, HHMMSS such as `12:30:15`, and a mix thereof such as `1 day 5h 30s`.

- [Installation](#installation)
- [Usage](#usage)
    - [Basic](#basic)
    - [Advanced](#advanced)
        - [FailureFlags](#failureflags)
        - [ParserSettings](#parsersettings)
        - [Guess the Locale](#guess-the-locale)
        - [Operations & Comparisons](#operations--comparisons)
- [Example Inputs](#example-inputs)
    - [Usage Notes](#usage-notes)
- [Supported Locales](#supported-locales)
- [Customization](#customization)

## Installation
`timelength` can be installed via pip:
```
pip install timelength
```
Or added to your project via poetry:
```
poetry add timelength
```

## Usage
### Basic
Import `TimeLength` and pass it a string to evaluate. As long as a single valid result is found the parsing will be considered a success regardless of any invalid content included in the input.
```python
from datetime import datetime, timezone
from timelength import TimeLength

tl = TimeLength("1.27 hours and 23 miles")
print(tl.result.success)
# True
print(tl.result.seconds)
# 4572.0
print(tl.to_minutes(max_precision=3))
# 76.2
print(tl.ago(base=datetime(2025, 1, 1, 0, 0, 0, 0, timezone.utc)))
# 2024-12-31 22:43:48+00:00
print(tl.hence(base=datetime(2025, 1, 1, 0, 0, 0, 0, timezone.utc)))
# 2025-01-01 01:16:12+00:00
print(tl.result.invalid)
# ((23.0, FailureFlags.LONELY_VALUE), ('miles', FailureFlags.UNKNOWN_TERM))
print(tl.result.valid)
# ((1.27, Scale(scale=3600.0, ...)),)
```

### Advanced
Control can be increased by making use of `FailureFlags` and `ParserSettings`. Both are passed to whichever `Locale` you are parsing with which is then passed to the `TimeLength` to be parsed.

`FailureFlags` is an IntFlag enum which holds all the currently possible reasons for a parse to fail. The default is `FailureFlags.NONE` which means as long as a single value is parsed, it will be considered a success. To achieve the opposite behavior, `FailureFlags.ALL` will cause the parsing to be considered a failure if any `FailureFlags` are detected, even if a valid value was parsed. See below for a full list.

`ParserSettings` is an object with various parsing settings. See below for a full list of options along with the default values.

In the first part of the example below, the flags are set to `(FailureFlags.LONELY_VALUE | FailureFlags.UNKNOWN_TERM)`, which means as long as a single valid item is found, the parsing will only be considered a failure if `FailureFlags.LONELY_VALUE` or `FailureFlags.UNKNOWN_TERM` show up in the invalid items. As `19` is included in the input without an accompanying scale, it is considered a `LONELY_VALUE` and thus invalid.

In the second part, the flags are reset, meaning nothing will cause parsing to be considered a failure as long as a single valid item is found. Additionally, the settings are updated such that duplicate scales are not allowed to be parsed. Due to this, `5m` from the input is added to the invalid items as a `DUPLICATE_SCALE` due to the preceding `35m`. Also, `19` is still in the invalid items as a `LONELY_VALUE`. Despite this, since the flags is set to `FailureFlags.NONE` and since `3.5d, 35m` is successfully parsed, the overall parsing is considered a success.
```python
from timelength import English, FailureFlags, ParserSettings, TimeLength

flags = (FailureFlags.LONELY_VALUE | FailureFlags.UNKNOWN_TERM)
locale = English(flags=flags)
tl = TimeLength("3.5d, 35m, 5m, 19", locale=locale)
print(tl.result.success)
# False
print(tl.result.invalid)
# ((19.0, FailureFlags.LONELY_VALUE),)
print(tl.result.valid)
# ((3.5, Scale(scale=86400.0, ...)), (35.0, Scale(scale=60.0, ...)), (5.0, Scale(scale=60.0, ...)))

flags = FailureFlags.NONE
settings = ParserSettings(allow_duplicate_scales=False)
locale.flags = flags
locale.settings = settings
tl.parse()
print(tl.result.success)
# True
print(tl.result.invalid)
# (('5m', FailureFlags.DUPLICATE_SCALE), (19.0, FailureFlags.LONELY_VALUE))
print(tl.result.valid)
# ((3.5, Scale(scale=86400.0, ...)), (35.0, Scale(scale=60.0, ...)))
```
To put it simply, `FailureFlags` is used to determine if an item that is in the invalid items tuple should invalidate the parsing as a whole, whereas `ParserSettings` is used to determine if certain customizable situations should even result in an item being added to the invalid items tuple to begin with.

### FailureFlags
The members of the `FailureFlags` IntEnum are:
- `NONE` — No failures will cause parsing to fail.
- `ALL` — Any failure will cause parsing to fail.
- `MALFORMED_CONTENT` — The fallback when something that shouldn't have happened, happened.
- `UNKNOWN_TERM` — The parsed value was not recognized from the terms or symbols in the config.
    - Ex: `1 mile`
- `MALFORMED_DECIMAL` — Multiple decimals were attempted within a singular decimal segment.
    - Ex: `1.2.3min`
- `MALFORMED_THOUSAND` — A thousand segment was attempted but did not have a leading number or a proper number of digits following a thousand separator.
    - Ex: `,234`, `1,23`, or `1,2345`
- `MALFORMED_FRACTION` — A fraction was attempted but had more than 2 values, a missing value, or was not formatted correctly.
    - Ex: `1/2/3`, `/2`, or `1+ / +2`
- `MALFORMED_HHMMSS` — An HH:MM:SS was attempted but had more segments than enabled scales or was not formatted correctly.
    - Ex: `1:2:3:4:5:6:7:8:9:10:11:12:13:14:15` or `1:15:26:`
- `LONELY_VALUE` — A value was parsed with no paired scale.
    - Ex: `one minute and twenty`
- `LONELY_SCALE` — A scale was parsed with no paired value.
    - Ex: `2 minutes and hours`
- `DUPLICATE_SCALE` — The same scale was parsed multiple times.
    - Ex: `1min 5:23` or `1min 5 minutes and 23 seconds`
- `CONSECUTIVE_CONNECTOR` — More than the allowed number of connectors were parsed in a row.
    - Ex: `1h    2min`
- `CONSECUTIVE_SEGMENTOR` — More than the allowed number of segmentors were parsed in a row.
    - Ex: `1h,, 2min`
- `CONSECUTIVE_SPECIAL` — More than the allowed number of special characters were parsed in a row.
    - Ex: `1h 2min!!`
- `MISPLACED_ALLOWED_TERM` — An allowed term was found in the middle of a segment/sentence.
    - Ex: `1!h 2min`
- `MISPLACED_SPECIAL` — A special character was found in the middle of a segment/sentence.
    - Ex: `1, /2`
- `UNUSED_OPERATION` — A term of the operation numeral was parsed but unused on any values.
    - Ex: `2 min of`
- `AMBIGUOUS_MULTIPLIERS` — More than one multiplier was parsed for a single segment which may be ambiguous.
    - Ex: `half of a quarter of two minutes and 30s`

### ParserSettings
- assume_scale: `Literal["LAST", "SINGLE", "NEVER"] = "SINGLE"` — How to handle no scale being provided.
    - `LAST` will assume seconds only for the last value if no scale is provided for it.
    - `SINGLE` will only assume seconds when a single input is provided.
    - `NEVER` will never assume seconds when no scale is provided.
- limit_allowed_terms: `bool = True` — Prevent terms from the `allowed_terms` list in
  the config from being used in the middle of a segment, thus interrupting a value/scale pair.
    - The affected segment will become abandoned and added to the invalid list.
    - The terms may still be used at the beginning or end of a segment/sentence.
    - If `False`, The terms will be ignored (within other limitations) and not effect parsing.
- allow_duplicate_scales: `bool = True` — Allow scales to be parsed multiple times, stacking their values.
    - If `False`, the first scale will be used and subsequent duplicates will be added to the invalid list.
- allow_thousands_extra_digits: `bool = False` — Allow thousands to be parsed with more than three digits following a thousand delimiter.
    - Ex: `1,2345` will be interpreted as `12,345`.
- allow_thousands_lacking_digits: `bool = False` — Allow a number to be parsed with less than three digits following a thousand delimiter.
    - Ex: `1,23` will be interpreted as `123`.
- allow_decimals_lacking_digits: `bool = True` — Allow decimals to be parsed with no number following the
  decimal delimiter.
    - Ex: `1.` will be interpreted as `1.0`.

### Guess the Locale
If you're unsure of which locale the input will belong to, you can attempt to guess the locale from the available options.
```python
from timelength import English, Spanish, Guess, TimeLength

guess = Guess()
tl = TimeLength("5 minutos", locale=guess)
print(tl.locale)
# Spanish
print(tl.result.success)
# True
print(tl.result.valid)
# ((5.0, Scale(scale=60.0, ...)))

tl.content = "5 minutes"
tl.parse(guess_locale=guess) # or `guess_locale=True`
print(tl.locale)
# English
print(tl.result.success)
# True
print(tl.result.valid)
# ((5.0, Scale(scale=60.0, ...)))
```
To guess the locale you can pass in an instantiated `Guess` either on creation of the `TimeLength` or to the `parse()` function on subsequent calls. Doing so will save locale instantiations as with each new `Guess` created, each locale available is instantiated in `Guess().locales`. Alternatively, for `parse()`, you can pass `True` for `guess_locale` and a new `Guess` will be instantiated automatically.

Guessing works by parsing with each locale. The one with the least invalid results is considered the correct locale. Ties are broken by most valid followed by alphabetically.

Any flags or settings passed to the `Guess` will be passed on to each locale. If none are provided, the defaults in each locale's configs are used. If you need to specify flags or settings per locale, you can directly access `Guess().locales`, which is a list of instantiated versions of all of the currently available locales.

If you have any custom locales you would like to be included in the possible results, append to `Guess().locales` before passing it to the `TimeLength` or `parse()` function.

### Operations & Comparisons
`TimeLength` objects support various arithmetic operations and comparisons between each other, datetimes, timedelta, and numbers. The supported options are:

1. **Addition**
    - `TimeLength` + `TimeLength` or `timedelta` or number -> `TimeLength`
    - `datetime` or `timedelta` + `TimeLength` -> `datetime` or `timedelta`

2. **Subtraction**
    - `TimeLength` - `TimeLength` or `timedelta` or number -> `TimeLength`
    - `datetime` or `timedelta` - `TimeLength` -> `datetime` or `timedelta`

3. **Multiplication**
    - `TimeLength` * number -> `TimeLength`
    - number * `TimeLength` -> `TimeLength`

4. **Division**
    - `TimeLength` / `TimeLength` or `timedelta` or number -> `TimeLength` or `float`
    - `timedelta` / `TimeLength` -> `float`

5. **Floor Division**
    - `TimeLength` // `TimeLength` or `timedelta` or number -> `TimeLength` or `float`
    - `timedelta` // `TimeLength` -> `float`

6. **Modulo**
    - `TimeLength` % `TimeLength` or `timedelta` -> `TimeLength`
    - `timedelta` % `TimeLength` -> `timedelta`

7. **Divmod**
    - `divmod(TimeLength, TimeLength or timedelta)` -> `tuple[float, TimeLength]`
    - `divmod(timedelta, TimeLength)` -> `tuple[float, timedelta]`

8. **Power**
    - `TimeLength` ** number -> `TimeLength` (optionally moduloed by `TimeLength` or `timedelta`)

9. **Comparisons**
    - `TimeLength` > `TimeLength` or `timedelta` -> `bool`
    - `TimeLength` >= `TimeLength` or `timedelta` -> `bool`
    - `TimeLength` < `TimeLength` or `timedelta` -> `bool`
    - `TimeLength` <= `TimeLength` or `timedelta` -> `bool`
    - `TimeLength` == `TimeLength` or `timedelta` -> `bool`
    - `TimeLength` != `TimeLength` or `timedelta` -> `bool`

10. **Other Operations**
    - `abs(TimeLength)` -> `TimeLength` (returns `self` unchanged as `TimeLength` is an absolute measurement)
    - `+TimeLength` -> `TimeLength` (returns `self` unchanged)
    - `-TimeLength` -> `TimeLength` (returns `self` unchanged)
    - `bool(TimeLength)` -> `bool` (returns `True` if parsing succeeded, otherwise `False`)
    - `len(TimeLength)` -> `int` (returns the length of `self.content`)

## Example Inputs
- `1m`
- `1min`
- `1 Minute`
- `1m and 2 SECONDS`
- `3h, 2 min, 3sec`
- `1.2d`
- `1,234s`
- `one hour`
- `twenty-two hours and thirty five minutes`
- `half of a day`
- `1/2 of a day`
- `1/4 hour`
- `1 Day, 2:34:12`
- `1:2:34:12`
- `1:5:13:27:22`

### Usage Notes
1. **Numerals**
    - Segmentors are ignored when parsing numerals in order to achieve consistency over ambiguity.
2. **Multipliers**
    - A single multiplier (ex: `half`) is allowed per segment (value + scale). This is due to the ambiguity introduced when more than one multiplier is used. May be revisited in the future if a good way to handle this ambiguity is found.
3. **HHMMSS**
    - It is not strictly adherent to typical `HH:MM:SS` standards. Any parsable numbers work in each slot, whether they are single digits, multiple digits, or include decimals.
        - For example, `2.56:27/3:270:19.2231` is a valid input in place of `2.56 days, 9 hours, 270 minutes, and 19.2231 seconds`.
        - It also accepts a single connector, such as a space, between deliminators. Example: `2: 6: 3`.
    - Supports up to as many segments as there are scales defined, including custom scales (10 default, `Millisecond` to `Century`).
        - The segments are parsed in reverse order, so smallest to largest (the order defined in the config and therefore the order loaded into the `Locale`, may differ for custom defined `Scale`s) to ensure the correct scales are applied.
            - EXCEPTION: The default base from which `HH:MM:SS` starts at is `Second`. Any scales (typically of lesser value) listed prior in the config, or appended to the scales list before `Second` in the case of custom scales, will not be utilized unless `Second` is disabled or as many `HH:MM:SS` segments are parsed as there are scales defined.
            - `12:30:15` is `12 hours, 30 minutes, and 15 seconds`, NOT `12 minutes, 30 seconds, and 15 milliseconds`.
            - `1:10:100:12:52:30:24:60:60:1000` will make use of `Century` to `Millisecond`.

## Supported Locales
1. English
2. Spanish
3. Basic Custom 
    - Copy & modify an existing config with new terms as long as your new `Locale` follows the existing config parser's grammar structure
4. Advanced Custom
    - Write your own parsing logic if your `Locale`'s grammar structure differs too drastically (PRs welcome)

### Customization
`timelength` allows for customizing the parsing behavior through JSON configuration. To get started, copy an existing locale JSON in `timelength/locales/`. The custom JSON may be placed anywhere.

**Ensure the JSON being used is from a trusted source, as the parser is loaded dynamically based on the file specified in the JSON. This could allow for unintended code execution if an unsafe config is loaded.**

Valid JSONs must include the following keys: 
- `connectors`
    - Characters/words that join two parts of the same segment.
    - Must have at least one value.
- `segmentors`
    - Characters/words that separate an input into segments.
    - Must have at least one value.
- `allowed_terms`
    - Characters or terms that won't be categorized as an invalid input. If sent multiple times in a row (ex: `!!`), they will still be marked as invalid. If `ParserSettings().limit_allowed_terms` is set then these characters won't be allowed in the middle of a segment (ex: `1!min`) and will cause the segment progress to reset.
- `hhmmss_delimiters`
    - Characters used to form `HH:MM:SS` segments. Can't have overlap with `decimal_delimiters`, `thousand_delimiters`, or `fraction_delimiters`.
- `decimal_delimiters`
    - Characters used to separate decimals from digits. Can't have overlap with `hhmmss_delimiters`, `thousand_delimiters`, or `fraction_delimiters`.
- `thousand_delimiters`
    - Characters used to break up large numbers. Can't have overlap with `hhmmss_delimiters`, `decimal_delimiters`, or `fraction_delimiters`.
- `fraction_delimiters`
    - Characters used to break form fractions. Can't have overlap with `hhmmss_delimiters`, `decimal_delimiters`, or `thousand_delimiters`.
- `parser_file`
    - The name of this locale's parser file (extension included) located in `timelength/parsers/`, or the path to the parser file if stored elsewhere. 
    - **Ensure only a trusted file is used as this could allow unintended code execution.**
    - The internal parser method must share a name with the file. Example: `parser_one.py` and `def parser_one()`.
- `scales`
    - Periods of time. The defaults are `millisecond`, `second`, `minute`, `hour`, `day`, `week`, `month`, `year`, `decade`, and `century`. Default scales must be present. At least one scale must be valid and enabled. Custom scales can be added following the format of the others. The following keys must be present and populated:
        - scale
            - The number of seconds this scale represents.
        - singular
           - The lowercase singular form of this scale.
        - plural
           - The lowercase plural form of this scale.
        - terms
          - All terms that could be parsed as this scale. Accents and other NFKD markings should not be present as they are filtered from the user input.
    - The following key is optional to disable a scale without removing it from the config:
        - enabled
            - A bool indicating if the scale is enabled or not.
- `numerals`
    - Word forms of numbers. May be populated or left empty. Each element must itself have the following keys, even if their contents are not used:
        - `type`
            - The numeral type.
        - `value`
            - The numerical value of this numeral.
        - `terms`
            - Characters/words that parse to this numeral's value.
- `flags`
    - A list of `FailureFlags` which will cause parsing to be considered a failure. Values should be upper cased. This is optional and can be passed to the locale dynamically instead. See a full list of options in the [FailureFlags](#failureflags) section.
- `settings`
    - A dictionary of options to modify parsing behavior. Each key should have a string or boolean value as appropriate. This is optional and can be passed to the locale dynamically instead. See a full list of options in the [ParserSettings](#parsersettings) section.
- `extra_data`
    - Any data a parser needs that is not already covered. May be populated or left empty. The locale loads this into a `Locale().extra_data` attribute, leaving the parser to utilize it.

Once your custom JSON is filled out, you can use it as follows:
```python
from timelength import TimeLength, Locale

output = TimeLength("30 minutes", locale = Locale("path/to/config.json"))
```
If all goes well, the parsing will succeed, and if not, an error will point you in the right direction.
