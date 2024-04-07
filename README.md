# timelength
A Python package to parse human readable lengths of time, including long form such as `1 day, 5 hours, and 30 seconds`, short form such as `1d5h30s`, a mix thereof such as `1 day 5h 30s`, and numerals such as `half a day` and `twelve hours`.

## Installation
`timelength` can be installed via pip:
```
pip install timelength
```
Or added to your project via poetry:
```
poetry add timelength
```

## Usage (English)
### Default
While `TimeLength.strict` is `False` (default), `TimeLength.result.success` will be `True` if at least one valid result is found, regardless of invalid results.
```python
from timelength import TimeLength

output = TimeLength("1d5h25m and 23miles")
print(output.result.success)
# True
print(output.result.seconds)
# 105900.0
print(output.to_minutes(max_precision = 3))
# 1765.0
print(output.result.invalid)
# [('miles', 'UNKNOWN_TERM'), (23.0, 'LONELY_VALUE')]
print(output.result.valid)
# [(1.0, Scale(86400.0, "day", "days")), (5.0, Scale(3600.0, "hour", "hours")), (25.0, Scale(60.0, "minute", "minutes"))]
```
Additionally, if a single lone value is parsed without a paired scale, seconds will be assumed. However, if more than one value is parsed, nothing will be assumed.
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
### Strict
While `TimeLength.strict` is `True`, `TimeLength.result.success` will only be `True` if at least one valid result is found and no invalid results are found.
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
Additionally, unlike with the default behavior, scales must be present. No assumptions will be made.

## Supported Locales
1. English
2. Spanish
3. Custom (Copy & modify an existing config with new terms as long as your new `Locale` follows the existing config parser's grammar structure)
4. Custom (Write your own parsing logic if your `Locale`'s grammar structure differs too drastically) (PRs welcome)

## Customization
`timelength` allows for customizing the parsing behavior through JSON configuration. To get started, copy an existing locale JSON in `timelength/locales/`. The custom JSON may be placed anywhere.

**Ensure the JSON being used is from a trusted source, as the parser is loaded dynamically based on the file specified in the JSON. This could allow for unintended code execution if an unsafe config is loaded.**

Valid JSONs must include the following keys, even if their contents are empty: 
- `connectors`
  - Characters/phrases that join two parts of the same segment.
- `segmentors`
  - Characters/phrases that join two segments together.
- `allowed_terms`
  - Characters or terms that won't be categorized as an invalid input. If sent multiple times in a row (ex: !!), they will still be marked as invalid.
- `decimal_separators`
  - Characters used to separate decimals from digits. Can't have overlap with `thousand_separators`.
- `thousand_separators`
  - Characters used to break up large numbers. Can't have overlap with `decimal_separators`.
- `parser_file`
  - The name of this locale's parser file (extension included) located in `timelength/parsers/`, or the path to the parser file if stored elsewhere. 
  - **Ensure only a trusted file is used as this could allow unintended code execution.**
  - The internal parser method must share a name with the file.
- `numerals`
  - Word forms of numbers. May be populated or left empty. Each element must itself have the following keys, even if their contents are not used:
    - `type`
      - The numeral type.
    - `value`
      - The numerical value of this numeral.
    - `terms`
      - Characters/phrases that parse to this numeral's value.
- `scales`
  - Periods of time. The defaults are `millisecond`, `second`, `minute`, `hour`, `day`, `week`, `month`, `year`, `decade`, and `century`. Default scales can be disabled by removing their entry completely. In their place an empty scale with no terms will be created. Custom scales can be added following the format of the others. The following keys must be present and populated:
    - scale
      - The number of seconds this scale represents.
    - singular
      - The lowercase singular form of this scale.
    - plural
      - The lowercase plural form of this scale.
    - terms
      - All terms that could be parsed as this scale. Accents and other NFKD markings should not be present as they are filtered from the user input.
- `extra_data`
  - Any data a parser needs that is not already covered. May be populated or left empty. The locale loads this into a `Locale._extra_data` attribute, leaving the parser to utilizes it.

Once your custom JSON is filled out, you can use it as follows:
```python
from timelength import TimeLength, CustomLocale

output = TimeLength("30 minutes", locale = CustomLocale("path/to/config.json"))
```
If all goes well, the parsing will succeed, and if not, an error will point you in the right direction.
