# timelength
A Python package to parse human readable lengths of time into seconds, including long form durations such as `1 day, 5 hours, and 30 seconds`, short form durations such as `1d5h30s`, numerals such as `twelve hours`, HHMMSS such as `12:30:15`, and a mix thereof such as `1 day 5h 30s`.

## Installation
`timelength` can be installed via pip:
```
pip install timelength
```
Or added to your project via poetry:
```
poetry add timelength
```

## Usage (English & Spanish)
### Default
While `TimeLength().strict` is `False` (default), `TimeLength().result.success` will be `True` if at least one valid result is found, regardless of invalid results.
```python
from timelength import TimeLength

output = TimeLength("1d5h25m15.5s and 23miles")
print(output.result.success)
# True
print(output.result.seconds)
# 105915.5
print(output.to_minutes(max_precision = 3))
# 1765.258
print(output.result.invalid)
# [('miles', 'UNKNOWN_TERM'), (23.0, 'LONELY_VALUE')]
print(output.result.valid)
# [(1.0, Scale(86400.0, "day", "days")), (5.0, Scale(3600.0, "hour", "hours")), (25.0, Scale(60.0, "minute", "minutes")), (15.5, Scale(1.0, "second", "seconds"))]
```
Additionally, if a single lone value is parsed without a paired scale, seconds will be assumed (if enabled, otherwise the lowest-value scale will be used). However, if more than one value is parsed, nothing will be assumed.
```python
output = TimeLength("45")
print(output.result.invalid)
# []
print(output.result.valid)
# [(45.0, Scale(1.0, "second", "seconds"))]

output = TimeLength("45 minutes, 33")
print(output.result.invalid)
# [(33.0, 'LONELY_VALUE')]
print(output.result.valid)
# [(45.0, Scale(60.0, "minute", "minutes"))]
```
And lastly, if multiple of the same `Scale`s are input, the cumulative will be calculated. For example, `2 minutes and 5 minutes` will return a total of 7 minutes.
```python
output = TimeLength("2 minutes and 5 minutes")
print(output.result.invalid)
# []
print(output.result.valid)
# [(2.0, Scale(60.0, "minute", "minutes")), (5.0, Scale(60.0, "minute", "minutes"))]
print(output.result.seconds)
# 420.0
```
### Strict
While `TimeLength().strict` is `True`, `TimeLength().result.success` will only be `True` if at least one valid result is found and no invalid results are found.
```python
from timelength import TimeLength

output = TimeLength("3.5d, 35m, 19", strict = True)
print(output.result.success)
# False
print(output.result.invalid)
# [(19.0, "LONELY_VALUE")]
print(output.result.valid)
# [(3.5, Scale(86400.0, "day", "days")), (35.0, Scale(60.0, "minute", "minutes"))]
```
Additionally, the following two behaviors are enacted:
1. Unlike with the default behavior, scales must be present. No assumptions will be made.
2. Multiples of the same `Scale` can't be used in the same input. For example, `2 minutes and 5 minutes` will cause `5 minutes` to be added to the `TimeLength().result.invalid` list rather than resulting in a cumulative 7 minutes.
```python
output = TimeLength("5", strict = True)
print(output.result.invalid)
# [(5.0, 'LONELY_VALUE')]
print(output.result.valid)
# []

output = TimeLength("2 minutes and 5 minutes", strict = True)
print(output.result.invalid)
# [('5.0 minutes', 'DUPLICATE_SCALE')]
print(output.result.valid)
# [(2.0, Scale(60.0, "minute", "minutes"))]
print(output.result.seconds)
# 120.0
```
### Invalid Results
Invalid results are found in `TimeLength().result.invalid`, which is a list of `tuple`s which themselves contain the invalid input and the reason it is invalid. The current invalid reasons can be found below:

0. `MALFORMED_CONTENT`
   - The fallback response when something that shouldn't have happened, happened.
1. `UNKNOWN_TERM`
   - The parsed value was not recognized from the terms or symbols set in the config.
2. `MALFORMED_DECIMAL`
    - Multiple decimals were attempted within a singular decimal segment, such as `12.5.6`.
3. `MALFORMED_THOUSAND`
    - A thousand segment was attempted but did not have a leading number or three digits following a thousand separator, such as `,75` or `1,25`.
4. `MALFORMED_HHMMSS`
    - The input for HH:MM:SS either had more segments than enabled scales, or was not formatted correctly, such as `2:5:`.
6. `LONELY_VALUE`
    - A value was parsed with no paired scale.
7. `CONSECUTIVE_VALUE`
    - Multiple values were parsed in a row.
8. `LONELY_SCALE`
    - A scale was parsed with no paired value.
9. `LEADING_SCALE`
    - A scale was parsed at the beginning of the input.
10. `CONSECUTIVE_SCALE`
    - Multiple scales were parsed in a row.
11. `CONSECUTIVE_CONNECTOR`
    - More than 2 connectors were parsed in a row (connectors have more leeway to allow for more formats).
12. `CONSECUTIVE_CONNECTOR`
    - Multiple segmentors were parsed in a row.
13. `CONSECUTIVE_SPECIAL`
    - Multiple special characters/phrases were parsed in a row.
14. `MISPLACED_SPECIAL`
    - `strict` was `True` and a member of the `allowed_terms` list was found in the middle of the content.
    - `allowed_terms` only exempts special characters/phrases from the end of segments or sentences.
15. `UNUSED_MULTIPLIER`
    - A multiplier was parsed in the content but unused on any values.
    - This refers to any term that is part of the `MULTIPLIER` numeral in the config.
16. `DUPLICATE_SCALE`
    - `strict` was `True` and a scale that was already used was parsed again.

This list is not guaranteed to remain consistent and may change as better descriptions are found or as parsing changes. If you plan to use these values to taylor your feedback to the user, it is recommended to have a default response in the case that the invalid reason returned is not one you have accounted for.
### Attributes
`TimeLength` contains these instance variables:
1. `content`
    - The string content representing the length of time.
2. `strict`
    - If `True`, then `result.success` will only return `True` if `result.valid` is populated and `result.invalid` is not populated during parsing. Also, `Scale`s may only appear once per input. If `False` (Default), then `result.success` will return `True` as long as `result.valid` has at least one item regardless of the state of `result.invalid` at the end of the parsing. Also, any duplicate `Scale`s will be added together for a cumulative result.
3. `locale`
    - The locale context used for parsing the time string. Defaults to `English`. Set to `None` to have the locale be guessed and the best result returned. If `strict` is `True`, the best result is the one with the least invalid results. If `strict` is `False`, the best result is the one with the most valid results. Add `CustomLocale`s to the locale pool by appending to `timelength.LOCALES`.
4. `result`
    - The result of the parsing, a `ParsedTimeLength` object.
      - `success`
        - Indicates if the parsing was successful. Determined by the strictness.
      - `seconds`
        - The total length of time parsed, in seconds.
      - `invalid`
        - A list of parts of the input string that could not be parsed as valid time.
      - `valid`
        - A list of parts of the input string that were successfully parsed as valid time.
5. `delta`
    - The total length of time parsed as a `timedelta`.
### Methods
1. `TimeLength().parse(guess_locale=False)`
    - Parses the current value of `TimeLength().content` with the current values of `TimeLength().strict` and `TimeLength().locale`. This is called during instantiation.
    - Pass `True` to `guess_locale` to try each available `Locale` and return the best result.
      - Add `CustomLocale`s to the locale pool by appending to `timelength.LOCALES`.
2. `TimeLength().to_seconds(max_precision=2)`
    - Converts the `TimeLength().result.seconds` to other  units with a max precision of `max_precision`.
    - Methods are available for `milliseconds` to `centuries` (all the default scales).
3. `TimeLength().ago(base=datetime.now(timezone.utc))`
    - Return a `datetime` in the past by `TimeLength().result.seconds`.
4. `TimeLength().hence(base=datetime.now(timezone.utc))`
    - Return a `datetime` in the future by `TimeLength().result.seconds`.
### Format Information
1. Numerals
    - Segmentors are largely ignored when parsing numerals in order to achieve consistency against ambiguity.
2. HHMMSS
    - It is not strictly adherent to typical `HH:MM:SS` standards. Any parsable numbers work in each slot, whether they are single digits, multiple digits, or include decimals.
      - For example, `2.56:9:270:19.2231` is a valid input in place of `2.56 days, 9 hours, 270 minutes, and 19.2231 seconds`.
      - It also accepts a single connector, such as a space, between deliminators. Example: `2: 6: 3`.
    - Supports up to as many segments as there are scales defined, including custom scales (10 default, `Millisecond` to `Century`).
      - The segments are parsed in reverse order, so smallest to largest (the order defined in the config and therefore the order loaded into the `Locale`, may differ for custom defined `Scale`s) to ensure the correct scales are applied.
      - EXCEPTION to `Millisecond`. Milliseconds only get their own segment if the full number of segments is used. Any fewer number of segments and the smallest scale applied is `Second`s, and milliseconds are expected to be a decimal attached to the seconds.

## Supported Locales
1. English
2. Spanish
3. Basic Custom (Copy & modify an existing config with new terms as long as your new `Locale` follows the existing config parser's grammar structure)
4. Advanced Custom (Write your own parsing logic if your `Locale`'s grammar structure differs too drastically) (PRs welcome)

## Customization
`timelength` allows for customizing the parsing behavior through JSON configuration. To get started, copy an existing locale JSON in `timelength/locales/`. The custom JSON may be placed anywhere.

**Ensure the JSON being used is from a trusted source, as the parser is loaded dynamically based on the file specified in the JSON. This could allow for unintended code execution if an unsafe config is loaded.**

Valid JSONs must include the following keys: 
- `connectors`
  - Characters/phrases that join two parts of the same segment.
  - Must have at least one value.
- `segmentors`
  - Characters/phrases that separate an input into segments.
  - Must have at least one value.
- `allowed_terms`
  - Characters or terms that won't be categorized as an invalid input even if `strict` is `True`. If sent multiple times in a row (ex: `!!`), they will still be marked as invalid. When `strict` is `True`, while they will not be marked as invalid, they will reset the segment progress. For example, if `!` is in the `allowed_terms` and an input of `two minutes!` is used, `!` will not be invalid. However, if an input of `two! minutes` is used, the progress will be reset at the `!` and `minutes` will become invalid with `LONELY_SCALE` and `two!` will become invalid with `MISPLACED_SPECIAL`. Of course, if `strict` is `False` it will parse just fine.
  - That is to say, this list is mainly to allow `strict` parsing not to fail with basic punctuation and to declutter the invalid list during `non-strict` parsing.
- `hhmmss_delimiters`
  - Characters used to form `HH:MM:SS` segments. Can't have overlap with `decimal_delimiters` or `thousand_delimiters`.
- `decimal_delimiters`
  - Characters used to separate decimals from digits. Can't have overlap with `hhmmss_delimiters` or `thousand_delimiters`.
- `thousand_delimiters`
  - Characters used to break up large numbers. Can't have overlap with `hhmmss_delimiters` or `decimal_delimiters`.
- `parser_file`
  - The name of this locale's parser file (extension included) located in `timelength/parsers/`, or the path to the parser file if stored elsewhere. 
  - **Ensure only a trusted file is used as this could allow unintended code execution.**
  - The internal parser method must share a name with the file. Example: `parser_one.py` and `def parser_one()`.
- `numerals`
  - Word forms of numbers. May be populated or left empty. Each element must itself have the following keys, even if their contents are not used:
    - `type`
      - The numeral type.
    - `value`
      - The numerical value of this numeral.
    - `terms`
      - Characters/phrases that parse to this numeral's value.
- `scales`
  - Periods of time. The defaults are `millisecond`, `second`, `minute`, `hour`, `day`, `week`, `month`, `year`, `decade`, and `century`. Default scales can be disabled by removing their entry completely. In their place an empty scale with no terms will be created. At least one scale must be present. Custom scales can be added following the format of the others. The following keys must be present and populated:
    - scale
      - The number of seconds this scale represents.
    - singular
      - The lowercase singular form of this scale.
    - plural
      - The lowercase plural form of this scale.
    - terms
      - All terms that could be parsed as this scale. Accents and other NFKD markings should not be present as they are filtered from the user input.
- `extra_data`
  - Any data a parser needs that is not already covered. May be populated or left empty. The locale loads this into a `Locale()._extra_data` attribute, leaving the parser to utilize it.

Once your custom JSON is filled out, you can use it as follows:
```python
from timelength import TimeLength, CustomLocale

output = TimeLength("30 minutes", locale = CustomLocale("path/to/config.json"))
```
If all goes well, the parsing will succeed, and if not, an error will point you in the right direction.
