# timelength
Inspired by [durations](https://github.com/oleiade/durations) by [oleiade](https://github.com/oleiade).

A Python package to parse human readable lengths of time, including long form such as `1 day, 5 hours, and 30 seconds`, short form such as `1d5h30s`, and a mix thereof such as `1 day 5h 30s`. Includes default relaxed parsing and optional strict parsing. Supports custom abbreviations, scale factors, and more.

## Installation
`timelength` can be installed via pip:
```bash
$ pip install timelength
```

## Usage
To parse a length of time, instantiate a TimeLength object with the string of text to parse. The text should include pairs of `Values` and `Scales`.
* A `Value` is a number.
* A `Scale` is a length of time from Milliseconds to Centuries, including short form and various other potential abbreviations associated with each scale.
* Acceptable separators of multiple  `Values` and `Scales` are commas, the word "`and`", normal spaces, and tab characters.

### Scale Reference
* Millisecond: `ms`, `millisecond`, `milliseconds`
* Second: `s`, `second`, `seconds`
* Minute:`m`, `minute`, `minutes`
* Hour: `h`, `hour`, `hours`
* Day: `d`, `day`, `days`
* Week: `w`, `week`, `weeks`
* Month: `M`, `month`, `months`
* Year: `y`, `year`, `years`
* Decade: `D`, `decade`, `decades`
* Century: `c`, `century`, `centuries`
* Various other abbreviations viewable with `timelength.Day().terms` etc

### Usage Example
```python
from timelength import TimeLength

time_string = "5.5min, and 10 seconds"

parsed_lenth = TimeLength(time_string)
parsed_lenth.total_seconds
# >>> 340.0
parsed_lenth.to_hours()
# >>> 0.09
parsed_lenth.to_hours(max_precision = 5)
# >>> 0.09444
parsed_lenth.strict
# >>> False
parsed_lenth.passed_value
# >>> 5.5min, and 10 seconds
parsed_lenth.parsed_value.valid
# >>> [(5.5, 'minutes'), (10.0, 'seconds')]
parsed_lenth.parsed_value.hours
# >>> None
parsed_lenth.parsed_value.minutes
# >>> 5.5
parsed_lenth.parsed_value.seconds
# >>> 10

time_string = "5 ish minutes and uhhh, 7 seconds?"

parsed_lenth = TimeLength(time_string)
parsed_lenth.to_seconds()
# >>> 307.0
parsed_lenth = TimeLength(time_string, strict = True)
# >>> InvalidValue: ... contains invalid values: ['ish', 'uhhh', '?']
```
```python
from timelength import TimeLength, Minute
from copy import deepcopy

time_string = "5.5MiNuTeS, and 10 seconds"
minute = deepcopy(Minute())
minute.terms.append("MiNuTeS")

parsed_lenth = TimeLength(time_string, custom_minute = minute)
parsed_lenth.total_seconds
# >>> 340.0
parsed_lenth.total_seconds
# >>> 5.5MiNuTeS, and 10 seconds
```