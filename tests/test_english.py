import pytest

from timelength.errors import (
    InvalidValue,
    LeadingScale,
    MultipleConsecutiveScales,
    MultipleConsecutiveSpecials,
    MultipleConsecutiveValues,
    NoValidValue,
)
from timelength.locales import English
from timelength.timelength import TimeLength
from timelength.dataclasses import Scale


@pytest.fixture
def tl_notstrict():
    return TimeLength(content="0 seconds", strict=False, locale=English())


@pytest.fixture
def tl_strict():
    return TimeLength(content="0 seconds", strict=True, locale=English())


def generate_notstrict_tests():
    cases = []
    # Basic Functionality
    cases.append(("", False, 0, [], []))
    cases.append(
        (
            "AHHHHH, what???###",
            False,
            0,
            [
                ("AHHHHH", "UNKNOWN_TERM"),
                ("what", "UNKNOWN_TERM"),
                ("###", "UNKNOWN_TERM"),
            ],
            [],
        )
    )
    cases.append(("0", True, 0, [], [(0, Scale(scale=1))]))
    cases.append(("5 seconds", True, 5, [], [(5, Scale(scale=1))]))
    cases.append(("5 seconds 3", True, 5, [], [(5, Scale(scale=1))]))
    for decimal in English()._decimal_separators:
        cases.append((f"5{decimal}5 seconds", True, 5.5, [], [(5.5, Scale(scale=1))]))
    for thousand in English()._thousand_separators:
        cases.append((f"5{thousand}500 seconds", True, 5500, [], [(5500, Scale(scale=1))]))
    for thousand in English()._thousand_separators:
        for decimal in English()._decimal_separators:
            cases.append(
                (
                    f"5{thousand}500{decimal}55 seconds",
                    True,
                    5500.55,
                    [],
                    [(5500.55, Scale(scale=1))],
                )
            )
    cases.append(
        ("1h5m30s", True, 3930, [], [(1, Scale(scale=3600)), (5, Scale(scale=60)), (30, Scale(scale=1))])
    )
    cases.append(
        (
            "1 hour 5 minutes 30 seconds",
            True,
            3930,
            [],
            [(1, Scale(scale=3600)), (5, Scale(scale=60)), (30, Scale(scale=1))],
        )
    )
    cases.append(
        (
            "1 hour 5min30s",
            True,
            3930,
            [],
            [(1, Scale(scale=3600)), (5, Scale(scale=60)), (30, Scale(scale=1))],
        )
    )

    # Segmentors as of Writing: "," "and" "&"
    cases.append(
        (
            "1 hour, 5 minutes, and 30 seconds & 7ms",
            True,
            3930.007,
            [],
            [(1, Scale(scale=3600)), (5, Scale(scale=60)), (30, Scale(scale=1)), (7, Scale(scale=0.001))],
        )
    )
    cases.append(("5m,, 5s", True, 305, [], [(5, Scale(scale=60)), (5, Scale(scale=1))]))
    cases.append(("1, 2, 3 minutes", True, 360, [], [(6, Scale(scale=60))]))
    # Connectors as of Writing: " ", "-", "\t"
    cases.append(
        (
            "1 minute-2-seconds	3MS",
            True,
            62.003,
            [],
            [(1, Scale(scale=60)), (2, Scale(scale=1)), (3, Scale(scale=0.001))],
        )
    )

    # Numerals / Modifiers / Multipliers
    cases.append(("zero", True, 0, [], [(0, Scale(scale=1))]))
    cases.append(("zero minutes", True, 0, [], [(0, Scale(scale=60))]))
    cases.append(("five", True, 5, [], [(5, Scale(scale=1))]))
    cases.append(("twenty-two sec", True, 22, [], [(22, Scale(scale=1))]))
    cases.append(("thousand seconds", True, 1000, [], [(1000, Scale(scale=1))]))
    cases.append(("a million seconds", True, 1000000, [], [(1000000, Scale(scale=1))]))
    cases.append(("half a million seconds", True, 500000, [], [(500000, Scale(scale=1))]))
    cases.append(
        (
            "third of a billion seconds",
            True,
            333333333.3333333,
            [],
            [(333333333.3333333, Scale(scale=1))],
        )
    )
    cases.append(("one million half seconds", True, 500000, [], [(500000, Scale(scale=1))]))
    cases.append(
        ("one million of half seconds", True, 500000, [], [(500000, Scale(scale=1))])
    )
    cases.append(("one half of minutes", False, 0, [("minutes", "LONELY_SCALE")], []))
    for item in English()._numerals["modifier_multiplier"]["terms"]:
        cases.append((f"two {item} six minutes", True, 360, [], [(6, Scale(scale=60))]))

    # Numeral Type Combinations + Float/Numeral Combinations
    cases.append(
        (
            "FIVE hours, 2 minutes, 3s",
            True,
            18123,
            [],
            [(5, Scale(scale=3600)), (2, Scale(scale=60)), (3, Scale(scale=1))],
        )
    )
    cases.append(("1 2 seconds", True, 2, [], [(2, Scale(scale=1))]))
    cases.append(("one two seconds", True, 12, [], [(12, Scale(scale=1))]))
    cases.append(("1 two seconds", True, 2, [], [(2, Scale(scale=1))]))
    cases.append(("one 2 seconds", True, 2, [], [(2, Scale(scale=1))]))

    cases.append(("1 13 seconds", True, 13, [], [(13, Scale(scale=1))]))
    cases.append(("one thirteen seconds", True, 113, [], [(113, Scale(scale=1))]))
    cases.append(("1 thirteen seconds", True, 13, [], [(13, Scale(scale=1))]))
    cases.append(("one 13 seconds", True, 13, [], [(13, Scale(scale=1))]))

    cases.append(("1 50 seconds", True, 50, [], [(50, Scale(scale=1))]))
    cases.append(("one fifty seconds", True, 150, [], [(150, Scale(scale=1))]))
    cases.append(("1 fifty seconds", True, 50, [], [(50, Scale(scale=1))]))
    cases.append(("one 50 seconds", True, 50, [], [(50, Scale(scale=1))]))

    cases.append(("3 100 seconds", True, 3100, [], [(3100, Scale(scale=1))]))
    cases.append(("three hundred seconds", True, 300, [], [(300, Scale(scale=1))]))
    cases.append(("3 hundred seconds", True, 300, [], [(300, Scale(scale=1))]))
    cases.append(("three 100 seconds", True, 100, [], [(100, Scale(scale=1))]))
    cases.append(("three one hundred seconds", True, 3100, [], [(3100, Scale(scale=1))]))
    cases.append(("three 1 hundred seconds", True, 100, [], [(100, Scale(scale=1))]))
    cases.append(("3 one hundred seconds", True, 100, [], [(100, Scale(scale=1))]))

    cases.append(("15 5 seconds", True, 5, [], [(5, Scale(scale=1))]))
    cases.append(("fifteen five seconds", True, 5, [], [(5, Scale(scale=1))]))
    cases.append(("15 five seconds", True, 5, [], [(5, Scale(scale=1))]))
    cases.append(("fifteen 5 seconds", True, 5, [], [(5, Scale(scale=1))]))

    cases.append(("15 15 seconds", True, 15, [], [(15, Scale(scale=1))]))
    cases.append(("fifteen fifteen seconds", True, 1515, [], [(1515, Scale(scale=1))]))
    cases.append(("15 fifteen seconds", True, 15, [], [(15, Scale(scale=1))]))
    cases.append(("fifteen 15 seconds", True, 15, [], [(15, Scale(scale=1))]))

    cases.append(("15 20 seconds", True, 20, [], [(20, Scale(scale=1))]))
    cases.append(("fifteen twenty seconds", True, 1520, [], [(1520, Scale(scale=1))]))
    cases.append(("15 twenty seconds", True, 20, [], [(20, Scale(scale=1))]))
    cases.append(("fifteen 20 seconds", True, 20, [], [(20, Scale(scale=1))]))

    cases.append(("20 1 seconds", True, 1, [], [(1, Scale(scale=1))]))
    cases.append(("twenty one seconds", True, 21, [], [(21, Scale(scale=1))]))
    cases.append(("20 one seconds", True, 1, [], [(1, Scale(scale=1))]))
    cases.append(("twenty 1 seconds", True, 1, [], [(1, Scale(scale=1))]))

    cases.append(("20 15 seconds", True, 15, [], [(15, Scale(scale=1))]))
    cases.append(("twenty fifteen seconds", True, 2015, [], [(2015, Scale(scale=1))]))
    cases.append(("20 fifteen seconds", True, 15, [], [(15, Scale(scale=1))]))
    cases.append(("twenty 15 seconds", True, 15, [], [(15, Scale(scale=1))]))

    cases.append(("20 30 seconds", True, 30, [], [(30, Scale(scale=1))]))
    cases.append(("twenty thirty seconds", True, 2030, [], [(2030, Scale(scale=1))]))
    cases.append(("20 thirty seconds", True, 30, [], [(30, Scale(scale=1))]))
    cases.append(("twenty 30 seconds", True, 30, [], [(30, Scale(scale=1))]))

    # Remaining Error Tests (For Strict)
    cases.append(
        (
            "1 minute seconds",
            True,
            60,
            [("seconds", "CONSECUTIVE_SCALES")],
            [(1, Scale(scale=60))],
        )
    )
    cases.append(
        ("minute 1 seconds", True, 1, [("minute", "LEADING_SCALE")], [(1, Scale(scale=1))])
    )
    return cases


def generate_strict_tests():
    cases = []
    # Basic Functionality
    cases.append(("", False, 0, [], [], NoValidValue))
    cases.append(
        (
            "AHHHHH, what???###",
            False,
            0,
            [
                ("AHHHHH", "UNKNOWN_TERM"),
                ("what", "UNKNOWN_TERM"),
                ("###", "UNKNOWN_TERM"),
            ],
            [],
            InvalidValue,
        )
    )
    cases.append(("0", False, 0, [(0, "LONELY_VALUE")], [], InvalidValue))
    cases.append(("5 seconds", True, 5, [], [(5, Scale(scale=1))], None))
    cases.append(("5 seconds 3", False, 5, [(3, "LONELY_VALUE")], [(5, Scale(scale=1))], InvalidValue))
    for item in English()._decimal_separators:
        cases.append((f"5{item}5 seconds", True, 5.5, [], [(5.5, Scale(scale=1))], None))
    for item in English()._thousand_separators:
        cases.append((f"5{item}500 seconds", True, 5500, [], [(5500, Scale(scale=1))], None))
    for thousand in English()._thousand_separators:
        for decimal in English()._decimal_separators:
            cases.append(
                (
                    f"5{thousand}500{decimal}55 seconds",
                    True,
                    5500.55,
                    [],
                    [(5500.55, Scale(scale=1))],
                    None,
                )
            )
    cases.append(
        (
            "1h5m30s",
            True,
            3930,
            [],
            [(1, Scale(scale=3600)), (5, Scale(scale=60)), (30, Scale(scale=1))],
            None,
        )
    )
    cases.append(
        (
            "1 hour 5 minutes 30 seconds",
            True,
            3930,
            [],
            [(1, Scale(scale=3600)), (5, Scale(scale=60)), (30, Scale(scale=1))],
            None,
        )
    )
    cases.append(
        (
            "1 hour 5min30s",
            True,
            3930,
            [],
            [(1, Scale(scale=3600)), (5, Scale(scale=60)), (30, Scale(scale=1))],
            None,
        )
    )

    # Segmentors as of Writing: "," "and" "&"
    cases.append(
        (
            "1 hour, 5 minutes, and 30 seconds & 7ms",
            True,
            3930.007,
            [],
            [(1, Scale(scale=3600)), (5, Scale(scale=60)), (30, Scale(scale=1)), (7, Scale(scale=0.001))],
            None,
        )
    )
    cases.append(
        (
            "5m,, 5s",
            False,
            300,
            [(",", "CONSECUTIVE_SPECIALS")],
            [(5, Scale(scale=60))],
            MultipleConsecutiveSpecials,
        )
    )
    cases.append(("1, 2, 3 minutes", True, 360, [], [(6, Scale(scale=60))], None))
    # Connectors as of Writing: " ", "-", "\t"
    cases.append(
        (
            "1 minute-2-seconds	3MS",
            True,
            62.003,
            [],
            [(1, Scale(scale=60)), (2, Scale(scale=1)), (3, Scale(scale=0.001))],
            None,
        )
    )

    # Numerals / Modifiers / Multipliers
    cases.append(("zero", False, 0, [(0, "LONELY_VALUE")], [], InvalidValue))
    cases.append(("zero MINUTES", True, 0, [], [(0, Scale(scale=60))], None))
    cases.append(("five hours", True, 18000, [], [(5, Scale(scale=3600))], None))
    cases.append(("twenty-two sec", True, 22, [], [(22, Scale(scale=1))], None))
    cases.append(("thousand seconds", True, 1000, [], [(1000, Scale(scale=1))], None))
    cases.append(("a million seconds", True, 1000000, [], [(1000000, Scale(scale=1))], None))
    cases.append(
        ("half a million seconds", True, 500000, [], [(500000, Scale(scale=1))], None)
    )
    cases.append(
        (
            "third of a billion seconds",
            True,
            333333333.3333333,
            [],
            [(333333333.3333333, Scale(scale=1))],
            None,
        )
    )
    cases.append(
        ("one million half seconds", True, 500000, [], [(500000, Scale(scale=1))], None)
    )
    cases.append(
        ("one million of half seconds", True, 500000, [], [(500000, Scale(scale=1))], None)
    )
    cases.append(
        (
            "one half of minutes",
            False,
            0,
            [("minutes", "LONELY_SCALE")],
            [],
            InvalidValue,
        )
    )
    for item in English()._numerals["modifier_multiplier"]["terms"]:
        cases.append(
            (
                f"two {item} six minutes",
                False,
                0,
                [(item, "MISPLACED_MODIFIER_MULTIPLIER")],
                [],
                InvalidValue,
            )
        )

    # Numeral Type Combinations + Float/Numeral Combinations
    cases.append(
        (
            "FIVE hours, 2 minutes, 3s",
            True,
            18123,
            [],
            [(5, Scale(scale=3600)), (2, Scale(scale=60)), (3, Scale(scale=1))],
            None,
        )
    )
    cases.append(
        (
            "1 2 seconds",
            False,
            0,
            [(2, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(("one two seconds", True, 12, [], [(12, Scale(scale=1))], None))
    cases.append(
        (
            "1 two seconds",
            False,
            0,
            [("two", "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(
        (
            "one 2 seconds",
            False,
            0,
            [(2, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )

    cases.append(
        (
            "1 13 seconds",
            False,
            0,
            [(13, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(("one thirteen seconds", True, 113, [], [(113, Scale(scale=1))], None))
    cases.append(
        (
            "1 thirteen seconds",
            False,
            0,
            [("thirteen", "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(
        (
            "one 13 seconds",
            False,
            0,
            [(13, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )

    cases.append(
        (
            "1 50 seconds",
            False,
            0,
            [(50, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(("one fifty seconds", True, 150, [], [(150, Scale(scale=1))], None))
    cases.append(
        (
            "1 fifty seconds",
            False,
            0,
            [("fifty", "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(
        (
            "one 50 seconds",
            False,
            0,
            [(50, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )

    cases.append(("3 100 seconds", True, 3100, [], [(3100, Scale(scale=1))], None))
    cases.append(("three hundred seconds", True, 300, [], [(300, Scale(scale=1))], None))
    cases.append(("3 hundred seconds", True, 300, [], [(300, Scale(scale=1))], None))
    cases.append(
        (
            "three 100 seconds",
            False,
            0,
            [(100, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(
        ("three one hundred seconds", True, 3100, [], [(3100, Scale(scale=1))], None)
    )
    cases.append(
        (
            "three 1 hundred seconds",
            False,
            0,
            [(1, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(
        (
            "3 one hundred seconds",
            False,
            0,
            [("one", "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )

    cases.append(
        (
            "15 5 seconds",
            False,
            0,
            [(5, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(
        (
            "fifteen five seconds",
            False,
            0,
            [("five", "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(
        (
            "15 five seconds",
            False,
            0,
            [("five", "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(
        (
            "fifteen 5 seconds",
            False,
            0,
            [(5, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )

    cases.append(
        (
            "15 15 seconds",
            False,
            0,
            [(15, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(("fifteen fifteen seconds", True, 1515, [], [(1515, Scale(scale=1))], None))
    cases.append(
        (
            "15 fifteen seconds",
            False,
            0,
            [("fifteen", "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(
        (
            "fifteen 15 seconds",
            False,
            0,
            [(15, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )

    cases.append(
        (
            "15 20 seconds",
            False,
            0,
            [(20, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(("fifteen twenty seconds", True, 1520, [], [(1520, Scale(scale=1))], None))
    cases.append(
        (
            "15 twenty seconds",
            False,
            0,
            [("twenty", "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(
        (
            "fifteen 20 seconds",
            False,
            0,
            [(20, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )

    cases.append(
        (
            "20 1 seconds",
            False,
            0,
            [(1, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(("twenty one seconds", True, 21, [], [(21, Scale(scale=1))], None))
    cases.append(
        (
            "20 one seconds",
            False,
            0,
            [("one", "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(
        (
            "twenty 1 seconds",
            False,
            0,
            [(1, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )

    cases.append(
        (
            "20 15 seconds",
            False,
            0,
            [(15, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(("twenty fifteen seconds", True, 2015, [], [(2015, Scale(scale=1))], None))
    cases.append(
        (
            "20 fifteen seconds",
            False,
            0,
            [("fifteen", "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(
        (
            "twenty 15 seconds",
            False,
            0,
            [(15, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )

    cases.append(
        (
            "20 30 seconds",
            False,
            0,
            [(30, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(("twenty thirty seconds", True, 2030, [], [(2030, Scale(scale=1))], None))
    cases.append(
        (
            "20 thirty seconds",
            False,
            0,
            [("thirty", "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )
    cases.append(
        (
            "twenty 30 seconds",
            False,
            0,
            [(30, "CONSECUTIVE_VALUES")],
            [],
            MultipleConsecutiveValues,
        )
    )

    # Remaining Error Tests
    cases.append(
        (
            "1 minute seconds",
            False,
            60,
            [("seconds", "CONSECUTIVE_SCALES")],
            [(1, Scale(scale=60))],
            MultipleConsecutiveScales,
        )
    )
    cases.append(
        ("minute 1 seconds", False, 0, [("minute", "LEADING_SCALE")], [], LeadingScale)
    )
    return cases


def compare_scales(scale1, scale2):
    """Compare two Scale objects based on the `scale` attribute."""
    return scale1.scale == scale2.scale


@pytest.mark.parametrize(
    "input, expected_success, expected_seconds, expected_invalid, expected_valid",
    generate_notstrict_tests(),
)
def test_notstrict_mode(
    tl_notstrict,
    input,
    expected_success,
    expected_seconds,
    expected_invalid,
    expected_valid,
):
    tl_notstrict.content = input
    tl_notstrict.parse()
    assert tl_notstrict.result.success is expected_success
    assert tl_notstrict.result.seconds == expected_seconds
    assert tl_notstrict.result.invalid == expected_invalid
    for actual_scale, expected_scale in zip(tl_notstrict.result.valid, expected_valid):
        assert compare_scales(actual_scale[1], expected_scale[1])


@pytest.mark.parametrize(
    "input, expected_success, expected_seconds, expected_invalid, expected_valid, expected_error",
    generate_strict_tests(),
)
def test_strict_mode(
    tl_strict,
    input,
    expected_success,
    expected_seconds,
    expected_invalid,
    expected_valid,
    expected_error,
):
    tl_strict.content = input
    if expected_error:
        with pytest.raises(expected_error):
            tl_strict.parse()
    else:
        tl_strict.parse()
    assert tl_strict.result.success is expected_success
    assert tl_strict.result.seconds == expected_seconds
    assert tl_strict.result.invalid == expected_invalid
    for actual_scale, expected_scale in zip(tl_strict.result.valid, expected_valid):
        assert compare_scales(actual_scale[1], expected_scale[1])
