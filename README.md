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
```python
>>> from timelength import TimeLength
>>>
>>> output = TimeLength("1d5h and 23miles")
>>> print(output.result.success)
True
>>> print(output.result.seconds)
104453.0
>>> print(output.result.invalid)
[('miles', 'UNKNOWN_TERM')]
>>> print(output.result.valid)
[(1.0, Scale(86400, "day", "days")), (5.0, Scale(3600, "hour", "hours")), (30.0, Scale(1, "second", "seconds")), (23.0, Scale(1, "second", "seconds"))]
>>>
>>>
```

## Customization
...

## Supported Locales
1. English
2. Custom (Copy & modify an existing config with new terms as long as your new Locale follows the existing config parser's grammar structure)
3. Custom (Write your own parsing logic if your Locale's grammar structure differs too drastically) (PRs welcome)
