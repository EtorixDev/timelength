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
An example showing default functionality. Unparseable content is ignored. `output.result.success` will be `True` if any valid result is found while `strict` is `False` (default).
```python
from timelength import TimeLength

output = TimeLength("1d5h and 23miles")
print(output.result.success)
# True
print(output.result.seconds)
# 104400.0
print(output.result.invalid)
# [('miles', 'UNKNOWN_TERM'), (23.0, 'LONELY_VALUE')]
print(output.result.valid)
# [(1.0, Scale(86400, "day", "days")), (5.0, Scale(3600, "hour", "hours"))]
```
An example showing strict parsing. Unparseable content or content not adhering to a recognized format (ex: `Value Scale`) results in `output.result.invalid` to be populated, which in turn causes `output.result.success` to be `False`. Despite this, the rest of the attributes are still parsed and populated the same as if `strict` were set to `False`.
```python
from timelength import TimeLength

output = TimeLength("3.5d, 35m, 19", strict = True)
print(output.result.success)
# False
print(output.result.seconds)
# 304500.0
print(output.result.invalid)
# [(19.0, "LONELY_VALUE")]
print(output.result.valid)
# [(3.5, Scale(scale=86400.0, "day", "days")), (35.0, Scale(scale=60.0, "minute", "minutes"))]
```

## Customization
...

## Supported Locales
1. English
2. Custom (Copy & modify an existing config with new terms as long as your new Locale follows the existing config parser's grammar structure)
3. Custom (Write your own parsing logic if your Locale's grammar structure differs too drastically) (PRs welcome)
