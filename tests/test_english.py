import pytest
from timelength import English, FailureFlags, ParserSettings, Scale, TimeLength


@pytest.fixture
def tl_notstrict():
    return TimeLength(content="0 seconds", locale=English())


@pytest.fixture
def tl_strict():
    return TimeLength(content="0 seconds", locale=English(flags=FailureFlags.ALL, settings=ParserSettings(allow_duplicate_scales=False)))


def generate_notstrict_tests():
    cases = []

    # Basic Functionality
    cases.append(("", False, 0.0, (), ()))
    cases.append(("AHHHHH, what???###", False, 0.0, (("AHHHHH", FailureFlags.UNKNOWN_TERM), ("what", FailureFlags.UNKNOWN_TERM), ("?", FailureFlags.CONSECUTIVE_SPECIAL), ("?", FailureFlags.CONSECUTIVE_SPECIAL), ("###", FailureFlags.UNKNOWN_TERM)), ()))
    cases.append(("0", True, 0.0, (), ((0.0, Scale(scale=1.0)),)))
    cases.append(("5 seconds", True, 5.0, (), ((5.0, Scale(scale=1.0)),)))
    cases.append(("5 seconds 3", True, 5.0, ((3.0, FailureFlags.LONELY_VALUE),), ((5.0, Scale(scale=1.0)),)))

    for decimal in English().decimal_delimiters:
        cases.append((f"5{decimal}5 seconds", True, 5.5, (), ((5.5, Scale(scale=1.0)),)))

    for thousand in English().thousand_delimiters:
        cases.append((f"5{thousand}500 seconds", True, 5500.0, (), ((5500.0, Scale(scale=1.0)),)))

    for thousand in English().thousand_delimiters:
        for decimal in English().decimal_delimiters:
            cases.append((f"5{thousand}500{decimal}55 seconds", True, 5500.55, (), ((5500.55, Scale(scale=1.0)),)))

    cases.append(("1h5m30s", True, 3930.0, (), ((1.0, Scale(scale=3600.0)), (5.0, Scale(scale=60.0)), (30.0, Scale(scale=1.0)))))
    cases.append(("1 hour 5 minutes 30 seconds", True, 3930.0, (), ((1.0, Scale(scale=3600.0)), (5.0, Scale(scale=60.0)), (30.0, Scale(scale=1.0)))))
    cases.append(("1 hour 5min30s", True, 3930.0, (), ((1.0, Scale(scale=3600.0)), (5.0, Scale(scale=60.0)), (30.0, Scale(scale=1.0)))))

    # Segmentors as of Writing: "," "and" "&"
    cases.append(("1 hour, 5 minutes, and 30 seconds & 7ms", True, 3930.007, (), ((1.0, Scale(scale=3600.0)), (5.0, Scale(scale=60.0)), (30.0, Scale(scale=1.0)), (7.0, Scale(scale=0.001)))))
    cases.append(("5m,, 5s", True, 305.0, ((",", FailureFlags.CONSECUTIVE_SEGMENTOR),), ((5.0, Scale(scale=60.0)), (5.0, Scale(scale=1.0)))))
    cases.append(("1, 2, 3 minutes", True, 360.0, (), ((6.0, Scale(scale=60.0)),)))

    # Connectors as of Writing: " ", "-", "\t", "+"
    cases.append(("1 minute-2-seconds	3MS", True, 62.003, (), ((1.0, Scale(scale=60.0)), (2.0, Scale(scale=1.0)), (3.0, Scale(scale=0.001)))))
    cases.append(("5m,   5s", True, 305.0, ((" ", FailureFlags.CONSECUTIVE_CONNECTOR),), ((5.0, Scale(scale=60.0)), (5.0, Scale(scale=1.0)))))
    cases.append(("1++++++2 minutes", True, 120.0, ((1.0, FailureFlags.LONELY_VALUE), ("+", FailureFlags.CONSECUTIVE_CONNECTOR), ("+", FailureFlags.CONSECUTIVE_CONNECTOR), ("+", FailureFlags.CONSECUTIVE_CONNECTOR), ("+", FailureFlags.CONSECUTIVE_CONNECTOR)), ((2.0, Scale(scale=60.0)),)))
    cases.append(("1++2 minutes", True, 120.0, ((1.0, FailureFlags.LONELY_VALUE),), ((2.0, Scale(scale=60.0)),)))

    # Numerals / Multipliers / Operators
    cases.append(("zero", True, 0.0, (), ((0.0, Scale(scale=1.0)),)))
    cases.append(("zero minutes", True, 0.0, (), ((0.0, Scale(scale=60.0)),)))
    cases.append(("five", True, 5.0, (), ((5.0, Scale(scale=1.0)),)))

    cases.append(("one thousand", True, 1000.0, (), ()))
    cases.append(("one thousand and five", True, 1005.0, (), ()))
    cases.append(("one thousand seconds and five", True, 1000.0, ((5.0, FailureFlags.LONELY_VALUE),), ()))

    cases.append(("half", True, 0.5, (), ((0.5, Scale(scale=1.0)),)))
    cases.append(("half min", True, 30.0, (), ((0.5, Scale(scale=60.0)),)))
    cases.append(("one half", True, 0.5, (), ((0.5, Scale(scale=1.0)),)))
    cases.append(("twenty-three of half min", True, 690, (), ((11.5, Scale(scale=60)),)))
    cases.append(("twenty-three half of min", True, 690, (), ((11.5, Scale(scale=60)),)))
    cases.append(("half of twenty-three min", True, 690, (), ((11.5, Scale(scale=60)),)))
    cases.append(("half twenty-three min", True, 690, (), ((11.5, Scale(scale=60)),)))

    cases.append(("half half twenty three min", True, 1380.0, (("half half", FailureFlags.AMBIGUOUS_MULTIPLIER),), ((23.0, Scale(scale=60.0)),)))
    cases.append(("half of half of twenty three min", True, 1380.0, (("half of half", FailureFlags.AMBIGUOUS_MULTIPLIER),), ((23.0, Scale(scale=60.0)),)))
    cases.append(("half of half twenty three min", True, 1380.0, (("half of half", FailureFlags.AMBIGUOUS_MULTIPLIER),), ((23.0, Scale(scale=60.0)),)))
    cases.append(("half half of twenty three min", True, 1380.0, (("half half", FailureFlags.AMBIGUOUS_MULTIPLIER),), ((23.0, Scale(scale=60.0)),)))
    cases.append(("twenty-three of half half mins", False, 0.0, (("twenty-three of half half", FailureFlags.AMBIGUOUS_MULTIPLIER), ("mins", FailureFlags.LONELY_SCALE)), ()))
    cases.append(("twenty-three half half of min", False, 0.0, (("twenty-three half half", FailureFlags.AMBIGUOUS_MULTIPLIER), ("min", FailureFlags.LONELY_SCALE)), ()))
    cases.append(("a million seconds half", True, 1000000.0, ((0.5, FailureFlags.LONELY_VALUE),), ((1000000.0, Scale(scale=1.0)),)))
    cases.append(("a million seconds half of", True, 1000000.0, (("of", FailureFlags.UNUSED_OPERATOR), (0.5, FailureFlags.LONELY_VALUE)), ((1000000.0, Scale(scale=1.0)),)))

    cases.append(("twenty-two sec", True, 22.0, (), ((22.0, Scale(scale=1.0)),)))
    cases.append(("thousand seconds", True, 1000.0, (), ((1000.0, Scale(scale=1.0)),)))
    cases.append(("a million seconds", True, 1000000.0, (), ((1000000.0, Scale(scale=1.0)),)))
    cases.append(("half a million seconds", True, 500000.0, (), ((500000.0, Scale(scale=1.0)),)))
    cases.append(("half million seconds", True, 500000.0, (), ((500000.0, Scale(scale=1.0)),)))
    cases.append(("third of a billion seconds", True, 333333333.3333333, (), ((333333333.3333333, Scale(scale=1.0)),)))
    cases.append(("one million half seconds", True, 500000.0, (), ((500000.0, Scale(scale=1.0)),)))
    cases.append(("one million of half seconds", True, 500000.0, (), ((500000.0, Scale(scale=1.0)),)))
    cases.append(("one half of minutes", True, 30.0, (), ((0.5, Scale(scale=60.0)),)))
    cases.append(("one half minutes of", True, 30.0, (("of", FailureFlags.UNUSED_OPERATOR),), ((0.5, Scale(scale=60.0)),)))
    cases.append(("the half of a million seconds", True, 500000.0, (), ((500000.0, Scale(scale=1.0)),)))
    cases.append(("twenty-five hundred minutes and half of one million two hundred and fifty-six thousand seconds", True, 778000.0, (), ((2500.0, Scale(scale=60.0)), (628000.0, Scale(scale=1.0)))))

    cases.append(("two of six minutes", True, 720.0, (), ((12.0, Scale(scale=60.0)),)))
    cases.append(("2 of six minutes", True, 720.0, (), ((12.0, Scale(scale=60.0)),)))
    cases.append(("two of 6 minutes", True, 720.0, (), ((12.0, Scale(scale=60.0)),)))
    cases.append(("2 of", False, 0.0, (("of", FailureFlags.UNUSED_OPERATOR), (2.0, FailureFlags.LONELY_VALUE)), ()))

    # Numeral Type Combinations + Float/Numeral Combinations
    cases.append(("FIVE hours, 2 minutes, 3s", True, 18123.0, (), ((5.0, Scale(scale=3600.0)), (2.0, Scale(scale=60.0)), (3.0, Scale(scale=1.0)))))
    cases.append(("1 2 seconds", True, 2.0, ((1.0, FailureFlags.LONELY_VALUE),), ((2.0, Scale(scale=1.0)),)))
    cases.append(("one two seconds", True, 12.0, (), ((12.0, Scale(scale=1.0)),)))
    cases.append(("1 two seconds", True, 2.0, ((1.0, FailureFlags.LONELY_VALUE),), ((2.0, Scale(scale=1.0)),)))
    cases.append(("one 2 seconds", True, 2.0, ((1.0, FailureFlags.LONELY_VALUE),), ((2.0, Scale(scale=1.0)),)))

    cases.append(("1 13 seconds", True, 13.0, ((1.0, FailureFlags.LONELY_VALUE),), ((13.0, Scale(scale=1.0)),)))
    cases.append(("one thirteen seconds", True, 113.0, (), ((113.0, Scale(scale=1.0)),)))
    cases.append(("1 thirteen seconds", True, 13.0, ((1.0, FailureFlags.LONELY_VALUE),), ((13.0, Scale(scale=1.0)),)))
    cases.append(("one 13 seconds", True, 13.0, ((1.0, FailureFlags.LONELY_VALUE),), ((13.0, Scale(scale=1.0)),)))

    cases.append(("1 50 seconds", True, 50.0, ((1.0, FailureFlags.LONELY_VALUE),), ((50.0, Scale(scale=1.0)),)))
    cases.append(("one fifty seconds", True, 150.0, (), ((150.0, Scale(scale=1.0)),)))
    cases.append(("1 fifty seconds", True, 50.0, ((1.0, FailureFlags.LONELY_VALUE),), ((50.0, Scale(scale=1.0)),)))
    cases.append(("one 50 seconds", True, 50.0, ((1.0, FailureFlags.LONELY_VALUE),), ((50.0, Scale(scale=1.0)),)))

    cases.append(("3 100 seconds", True, 3100.0, (), ((3100.0, Scale(scale=1.0)),)))
    cases.append(("three hundred seconds", True, 300.0, (), ((300.0, Scale(scale=1.0)),)))
    cases.append(("3 hundred seconds", True, 300.0, (), ((300.0, Scale(scale=1.0)),)))
    cases.append(("three 100 seconds", True, 100.0, ((3.0, FailureFlags.LONELY_VALUE),), ((100.0, Scale(scale=1.0)),)))
    cases.append(("three one hundred seconds", True, 3100.0, (), ((3100.0, Scale(scale=1.0)),)))
    cases.append(("three 1 hundred seconds", True, 100.0, ((3.0, FailureFlags.LONELY_VALUE),), ((100.0, Scale(scale=1.0)),)))
    cases.append(("3 one hundred seconds", True, 100.0, ((3.0, FailureFlags.LONELY_VALUE),), ((100.0, Scale(scale=1.0)),)))

    cases.append(("15 5 seconds", True, 5.0, ((15.0, FailureFlags.LONELY_VALUE),), ((5.0, Scale(scale=1.0)),)))
    cases.append(("fifteen five seconds", True, 5.0, ((15.0, FailureFlags.LONELY_VALUE),), ((5.0, Scale(scale=1.0)),)))
    cases.append(("15 five seconds", True, 5.0, ((15.0, FailureFlags.LONELY_VALUE),), ((5.0, Scale(scale=1.0)),)))
    cases.append(("fifteen 5 seconds", True, 5.0, ((15.0, FailureFlags.LONELY_VALUE),), ((5.0, Scale(scale=1.0)),)))

    cases.append(("15 15 seconds", True, 15.0, ((15.0, FailureFlags.LONELY_VALUE),), ((15.0, Scale(scale=1.0)),)))
    cases.append(("fifteen fifteen seconds", True, 1515.0, (), ((1515.0, Scale(scale=1.0)),)))
    cases.append(("15 fifteen seconds", True, 15.0, ((15.0, FailureFlags.LONELY_VALUE),), ((15.0, Scale(scale=1.0)),)))
    cases.append(("fifteen 15 seconds", True, 15.0, ((15.0, FailureFlags.LONELY_VALUE),), ((15.0, Scale(scale=1.0)),)))

    cases.append(("15 20 seconds", True, 20.0, ((15.0, FailureFlags.LONELY_VALUE),), ((20.0, Scale(scale=1.0)),)))
    cases.append(("fifteen twenty seconds", True, 1520.0, (), ((1520.0, Scale(scale=1.0)),)))
    cases.append(("15 twenty seconds", True, 20.0, ((15.0, FailureFlags.LONELY_VALUE),), ((20.0, Scale(scale=1.0)),)))
    cases.append(("fifteen 20 seconds", True, 20.0, ((15.0, FailureFlags.LONELY_VALUE),), ((20.0, Scale(scale=1.0)),)))

    cases.append(("20 1 seconds", True, 1.0, ((20.0, FailureFlags.LONELY_VALUE),), ((1.0, Scale(scale=1.0)),)))
    cases.append(("twenty one seconds", True, 21.0, (), ((21.0, Scale(scale=1.0)),)))
    cases.append(("20 one seconds", True, 1.0, ((20.0, FailureFlags.LONELY_VALUE),), ((1.0, Scale(scale=1.0)),)))
    cases.append(("twenty 1 seconds", True, 1.0, ((20.0, FailureFlags.LONELY_VALUE),), ((1.0, Scale(scale=1.0)),)))

    cases.append(("20 15 seconds", True, 15.0, ((20.0, FailureFlags.LONELY_VALUE),), ((15.0, Scale(scale=1.0)),)))
    cases.append(("twenty fifteen seconds", True, 2015.0, (), ((2015.0, Scale(scale=1.0)),)))
    cases.append(("20 fifteen seconds", True, 15.0, ((20.0, FailureFlags.LONELY_VALUE),), ((15.0, Scale(scale=1.0)),)))
    cases.append(("twenty 15 seconds", True, 15.0, ((20.0, FailureFlags.LONELY_VALUE),), ((15.0, Scale(scale=1.0)),)))

    cases.append(("20 30 seconds", True, 30.0, ((20.0, FailureFlags.LONELY_VALUE),), ((30.0, Scale(scale=1.0)),)))
    cases.append(("twenty thirty seconds", True, 2030.0, (), ((2030.0, Scale(scale=1.0)),)))
    cases.append(("20 thirty seconds", True, 30.0, ((20.0, FailureFlags.LONELY_VALUE),), ((30.0, Scale(scale=1.0)),)))
    cases.append(("twenty 30 seconds", True, 30.0, ((20.0, FailureFlags.LONELY_VALUE),), ((30.0, Scale(scale=1.0)),)))
    cases.append(("twenty twenty three seconds", True, 2023.0, (), ((2023.0, Scale(scale=1.0)),)))
    cases.append(("twenty 20 three seconds", True, 3.0, ((20.0, FailureFlags.LONELY_VALUE), (20.0, FailureFlags.LONELY_VALUE)), ((3.0, Scale(scale=1.0)),)))
    cases.append(("twenty 20 3 seconds", True, 3.0, ((20.0, FailureFlags.LONELY_VALUE), (20.0, FailureFlags.LONELY_VALUE)), ((3.0, Scale(scale=1.0)),)))
    cases.append(("twenty 20 3", False, 0.0, ((20.0, FailureFlags.LONELY_VALUE), (20.0, FailureFlags.LONELY_VALUE), (3.0, FailureFlags.LONELY_VALUE)), ()))

    # Misc
    cases.append(("1 minute seconds", True, 60.0, (("seconds", FailureFlags.LONELY_SCALE),), ((1.0, Scale(scale=60.0)),)))
    cases.append(("minute 1 seconds", True, 1.0, (("minute", FailureFlags.LONELY_SCALE),), ((1.0, Scale(scale=1.0)),)))
    cases.append(("1, one 1", False, 0.0, ((1.0, FailureFlags.LONELY_VALUE), (1.0, FailureFlags.LONELY_VALUE), (1.0, FailureFlags.LONELY_VALUE)), ()))
    cases.append(("1!!!sec", False, 0.0, (("1!!!", FailureFlags.MISPLACED_ALLOWED_TERM), ("sec", FailureFlags.LONELY_SCALE)), ()))
    cases.append(("1, two/sec", False, 0.0, ((1.0, FailureFlags.LONELY_VALUE), (2.0, FailureFlags.LONELY_VALUE), ("/", FailureFlags.MISPLACED_SPECIAL), ("sec", FailureFlags.LONELY_SCALE)), ()))

    # Long Numerals + Segmentor Combinations
    cases.append(("twenty-three thousand sec", True, 23000.0, (), ((23000.0, Scale(scale=1.0)),)))
    cases.append(("two thousand twenty-three sec", True, 2023.0, (), ((30.0, Scale(scale=1.0)),)))
    cases.append(("two thousand twenty three five sec", True, 5.0, ((2023.0, FailureFlags.LONELY_VALUE),), ((5.0, Scale(scale=1.0)),)))
    cases.append(("two thousand twenty three thousand five sec", True, 23005.0, ((2000.0, FailureFlags.LONELY_VALUE),), ((23005.0, Scale(scale=1.0)),)))
    cases.append(("two thousand and twenty three five sec", True, 5.0, ((2023.0, FailureFlags.LONELY_VALUE),), ((5.0, Scale(scale=1.0)),)))
    cases.append(("one thousand five and hundred", True, 1500.0, (), ((1500.0, Scale(scale=1.0)),)))
    cases.append(("one thousand 5 and hundred", True, 1500.0, (), ((1500.0, Scale(scale=1.0)),)))

    cases.append(("one hundred seventy two thousand", True, 172000.0, (), ((172000.0, Scale(scale=1.0)),)))
    cases.append(("one hundred and seventy two thousand", True, 172000.0, (), ((172000.0, Scale(scale=1.0)),)))
    cases.append(("one million seventy two thousand", True, 1072000.0, (), ((1072000.0, Scale(scale=1.0)),)))
    cases.append(("one million and seventy two thousand", True, 1072000.0, (), ((1072000.0, Scale(scale=1.0)),)))
    cases.append(("one million seventy two thousand five hundred and six", True, 1072506.0, (), ((1072506.0, Scale(scale=1.0)),)))
    cases.append(("one million seventy and two thousand five hundred six", True, 1072506, (), ((1072506.0, Scale(scale=1.0)),)))
    cases.append(("one million seventy two thousand five hundred and six million", True, 1072506000000.0, (), ((1072506000000.0, Scale(scale=1.0)),)))
    cases.append(("one thousand six hundred     and five", False, 0.0, ((1600.0, FailureFlags.LONELY_VALUE), (" ", FailureFlags.CONSECUTIVE_CONNECTOR), (" ", FailureFlags.CONSECUTIVE_CONNECTOR), (" ", FailureFlags.CONSECUTIVE_CONNECTOR), (5.0, FailureFlags.LONELY_VALUE)), ()))
    cases.append(("five hundred and two hundred seconds", True, 700.0, (), ((700.0, Scale(scale=1.0)),)))
    cases.append(("one billion billion billion billion billion years", True, 3.1536000000000003e52, (), ((1.0000000000000001e45, Scale(scale=31536000.0)),)))

    # Awkward Thousands/Decimals
    cases.append(("twenty,18 three seconds", True, 3.0, ((20.0, FailureFlags.LONELY_VALUE), (18.0, FailureFlags.LONELY_VALUE)), ((3.0, Scale(scale=1.0)),)))
    cases.append(("twenty .18 three seconds", True, 3.0, ((20.0, FailureFlags.LONELY_VALUE), (0.18, FailureFlags.LONELY_VALUE)), ((3.0, Scale(scale=1.0)),)))
    cases.append(("twenty 18 three seconds", True, 3.0, ((20.0, FailureFlags.LONELY_VALUE), (18.0, FailureFlags.LONELY_VALUE)), ((3.0, Scale(scale=1.0)),)))

    # HHMMSS, Fractions, + Combinations
    cases.append(("12:30:15.25", True, 45015.25, (), ((12.0, Scale(scale=3600.0)), (30.0, Scale(scale=60.0)), (15.25, Scale(scale=1.0)))))
    cases.append(("22: 5", True, 1325.0, (), ((22.0, Scale(scale=60.0)), (5.0, Scale(scale=1.0)))))
    cases.append(("1:2:22:33 558:66:77.1234", True, 126558437.1234, (), ((1.0, Scale(scale=2635200.0)), (2.0, Scale(scale=604800.0)), (22.0, Scale(scale=86400.0)), (33558.0, Scale(scale=3600.0)), (66.0, Scale(scale=60.0)), (77.1234, Scale(scale=1.0)))))
    cases.append(("1 day 2:30:15.25", True, 95415.25, (), ((1.0, Scale(scale=86400.0)), (2.0, Scale(scale=3600.0)), (30.0, Scale(scale=60.0)), (15.25, Scale(scale=1.0)))))
    cases.append(("22: 2,455: 5555", True, 232055.0, (), ((22.0, Scale(scale=3600.0)), (2455.0, Scale(scale=60.0)), (5555.0, Scale(scale=1.0)))))
    cases.append(("22:  +2,455: 5555", False, 0.0, (("22:  +2,455: 5555", FailureFlags.MALFORMED_HHMMSS),), ()))
    cases.append(("22: 2,455 : 5555", False, 0.0, (("22: 2,455 : 5555", FailureFlags.MALFORMED_HHMMSS),), ()))
    cases.append(("22: 2,455 5: 5555", True, 9630.0, (), ((22.0, Scale(scale=60.0)), (2455.0, Scale(scale=1.0)), (5.0, Scale(scale=60.0)), (5555.0, Scale(scale=1.0)))))
    cases.append(("22: 2 455: +5555", True, 232055.0, (), ((22.0, Scale(scale=3600.0)), (2455.0, Scale(scale=60.0)), (5555.0, Scale(scale=1.0)))))
    cases.append(("22: 2,455: ++5555", False, 0.0, (("22: 2,455: ++5555", FailureFlags.MALFORMED_HHMMSS),), ()))
    cases.append(("2:55 5 minutes", True, 475.0, (), ((2.0, Scale(scale=60.0)), (55.0, Scale(scale=1.0)), (5.0, Scale(scale=60.0)))))
    cases.append(("2: 6 5: 2", True, 428.0, (), ((2.0, Scale(scale=60.0)), (6.0, Scale(scale=1.0)), (5.0, Scale(scale=60.0)), (2.0, Scale(scale=1.0)))))
    cases.append(("1/2 of a min", True, 30.0, (), ((0.5, Scale(scale=60.0)),)))
    cases.append(("1 / 2 of a min", True, 30.0, (), ((0.5, Scale(scale=60.0)),)))
    cases.append(("1+/+2 of a min", True, 30.0, (), ((0.5, Scale(scale=60.0)),)))
    cases.append(("+1 / +2 of a min", True, 60.0, (("1 / +2", FailureFlags.MALFORMED_FRACTION), ("of", FailureFlags.UNUSED_OPERATOR)), ((1.0, Scale(scale=60.0)),)))
    cases.append(("1 Day, 3:45:16.5", True, 99916.5, (), ((1.0, Scale(scale=86400.0)), (3.0, Scale(scale=3600.0)), (45.0, Scale(scale=60.0)), (16.5, Scale(scale=1.0)))))
    cases.append(("1:27/3:15.5:14", True, 119744.0, (), ((1.0, Scale(scale=86400.0)), (9.0, Scale(scale=3600.0)), (15.5, Scale(scale=60.0)), (14.0, Scale(scale=1.0)))))
    cases.append(("1+++/+++2 minutes", False, 0.0, (("1+++/+++2", FailureFlags.MALFORMED_FRACTION), ("minutes", FailureFlags.LONELY_SCALE)), ()))
    cases.append(("1+/+2 minutes", True, 30.0, (), ((0.5, Scale(scale=60.0)),)))
    cases.append(("1 / 2 / 3 minutes", False, 0.0, (("1 / 2 / 3", FailureFlags.MALFORMED_FRACTION), ("minutes", FailureFlags.LONELY_SCALE)), ()))
    cases.append(("1,2 /2..3 sec", False, 0.0, (("1,2 /2..3", FailureFlags.MALFORMED_DECIMAL | FailureFlags.MALFORMED_THOUSAND | FailureFlags.MALFORMED_FRACTION), ("sec", FailureFlags.LONELY_SCALE)), ()))
    cases.append(("1:1,2:1...4:6 sec", False, 0.0, (("1:1,2:1...4:6", FailureFlags.MALFORMED_DECIMAL | FailureFlags.MALFORMED_THOUSAND | FailureFlags.MALFORMED_HHMMSS), ("sec", FailureFlags.LONELY_SCALE)), ()))
    cases.append(("1/0 sec", False, 0.0, (("1/0", FailureFlags.MALFORMED_FRACTION), ("sec", FailureFlags.LONELY_SCALE)), ()))
    cases.append(("1:2::5", False, 0.0, (("1:2::5", FailureFlags.MALFORMED_HHMMSS),), ()))
    cases.append(("1:2/   3:1:5", False, 0.0, (("1:2/   3:1:5", FailureFlags.MALFORMED_FRACTION | FailureFlags.MALFORMED_HHMMSS),), ()))
    cases.append(("1:2:3:4:5:6:7:8:9:10:11", False, 0.0, (("1:2:3:4:5:6:7:8:9:10:11", FailureFlags.MALFORMED_HHMMSS),), ()))
    cases.append(("97 1:2:3", True, 3723.0, ((97.0, FailureFlags.LONELY_VALUE),), ((1.0, Scale(scale=3600.0)), (2.0, Scale(scale=60.0)), (3.0, Scale(scale=1.0)))))
    cases.append(("97, 5 1:2:3", True, 3723.0, ((97.0, FailureFlags.LONELY_VALUE), (5.0, FailureFlags.LONELY_VALUE)), ((1.0, Scale(scale=3600.0)), (2.0, Scale(scale=60.0)), (3.0, Scale(scale=1.0)))))
    cases.append(("97, half 5 1:2:3", True, 3723.0, ((97.0, FailureFlags.LONELY_VALUE), (0.5, FailureFlags.LONELY_VALUE), (5.0, FailureFlags.LONELY_VALUE)), ((1.0, Scale(scale=3600.0)), (2.0, Scale(scale=60.0)), (3.0, Scale(scale=1.0)))))

    # Duplicate Scales
    cases.append(("2 minutes and 3 minutes, 5 minutes", True, 600.0, (), ((2.0, Scale(scale=60.0)), (3.0, Scale(scale=60.0)), (5.0, Scale(scale=60.0)))))
    cases.append(("twenty hundred five seconds, twenty thousand seconds", True, 22005.0, (), ((2005.0, Scale(scale=1.0)), (20000.0, Scale(scale=1.0)))))
    cases.append(("twenty hundred five, twenty thousand seconds", True, 20000.0, ((2005.0, FailureFlags.LONELY_VALUE),), ((20000.0, Scale(scale=1.0)),)))

    return cases


def generate_strict_tests():
    cases = []

    # Basic Functionality
    cases.append(("", False, 0.0, (), ()))
    cases.append(("AHHHHH, what???###", False, 0.0, (("AHHHHH", FailureFlags.UNKNOWN_TERM), ("what", FailureFlags.UNKNOWN_TERM), ("?", FailureFlags.CONSECUTIVE_SPECIAL), ("?", FailureFlags.CONSECUTIVE_SPECIAL), ("###", FailureFlags.UNKNOWN_TERM)), ()))
    cases.append(("0", True, 0.0, (), ((0.0, Scale(scale=1.0)),)))
    cases.append(("5 seconds", True, 5.0, (), ((5.0, Scale(scale=1.0)),)))
    cases.append(("5 seconds 3", False, 5.0, ((3.0, FailureFlags.LONELY_VALUE),), ((5.0, Scale(scale=1.0)),)))

    for decimal in English().decimal_delimiters:
        cases.append((f"5{decimal}5 seconds", True, 5.5, (), ((5.5, Scale(scale=1.0)),)))

    for thousand in English().thousand_delimiters:
        cases.append((f"5{thousand}500 seconds", True, 5500.0, (), ((5500.0, Scale(scale=1.0)),)))

    for thousand in English().thousand_delimiters:
        for decimal in English().decimal_delimiters:
            cases.append((f"5{thousand}500{decimal}55 seconds", True, 5500.55, (), ((5500.55, Scale(scale=1.0)),)))

    cases.append(("1h5m30s", True, 3930.0, (), ((1.0, Scale(scale=3600.0)), (5.0, Scale(scale=60.0)), (30.0, Scale(scale=1.0)))))
    cases.append(("1 hour 5 minutes 30 seconds", True, 3930.0, (), ((1.0, Scale(scale=3600.0)), (5.0, Scale(scale=60.0)), (30.0, Scale(scale=1.0)))))
    cases.append(("1 hour 5min30s", True, 3930.0, (), ((1.0, Scale(scale=3600.0)), (5.0, Scale(scale=60.0)), (30.0, Scale(scale=1.0)))))

    # Segmentors as of Writing: "," "and" "&"
    cases.append(("1 hour, 5 minutes, and 30 seconds & 7ms", True, 3930.007, (), ((1.0, Scale(scale=3600.0)), (5.0, Scale(scale=60.0)), (30.0, Scale(scale=1.0)), (7.0, Scale(scale=0.001)))))
    cases.append(("5m,, 5s", False, 305.0, ((",", FailureFlags.CONSECUTIVE_SEGMENTOR),), ((5.0, Scale(scale=60.0)), (5.0, Scale(scale=1.0)))))
    cases.append(("1, 2, 3 minutes", True, 360.0, (), ((6.0, Scale(scale=60.0)),)))

    # Connectors as of Writing: " ", "-", "\t", "+"
    cases.append(("1 minute-2-seconds	3MS", True, 62.003, (), ((1.0, Scale(scale=60.0)), (2.0, Scale(scale=1.0)), (3.0, Scale(scale=0.001)))))
    cases.append(("5m,   5s", False, 305.0, ((" ", FailureFlags.CONSECUTIVE_CONNECTOR),), ((5.0, Scale(scale=60.0)), (5.0, Scale(scale=1.0)))))
    cases.append(("1++++++2 minutes", False, 120.0, ((1.0, FailureFlags.LONELY_VALUE), ("+", FailureFlags.CONSECUTIVE_CONNECTOR), ("+", FailureFlags.CONSECUTIVE_CONNECTOR), ("+", FailureFlags.CONSECUTIVE_CONNECTOR), ("+", FailureFlags.CONSECUTIVE_CONNECTOR)), ((2.0, Scale(scale=60.0)),)))
    cases.append(("1++2 minutes", False, 120.0, ((1.0, FailureFlags.LONELY_VALUE),), ((2.0, Scale(scale=60.0)),)))

    # Numerals / Multipliers / Operators
    cases.append(("zero", True, 0.0, (), ((0.0, Scale(scale=1.0)),)))
    cases.append(("zero minutes", True, 0.0, (), ((0.0, Scale(scale=60.0)),)))
    cases.append(("five", True, 5.0, (), ((5.0, Scale(scale=1.0)),)))

    cases.append(("one thousand", True, 1000.0, (), ((1000.0, Scale(scale=1.0)),)))
    cases.append(("one thousand and five", True, 1005.0, (), ((1005.0, Scale(scale=1.0)),)))
    cases.append(("one thousand seconds and five", False, 1000.0, ((5.0, FailureFlags.LONELY_VALUE),), ((1000.0, Scale(scale=1.0)),)))

    cases.append(("half", True, 0.5, (), ((0.5, Scale(scale=1.0)),)))
    cases.append(("half min", True, 30.0, (), ((0.5, Scale(scale=60.0)),)))
    cases.append(("one half", True, 0.5, (), ((0.5, Scale(scale=1.0)),)))
    cases.append(("twenty-three of half min", True, 690, (), ((11.5, Scale(scale=60)),)))
    cases.append(("twenty-three half of min", True, 690, (), ((11.5, Scale(scale=60)),)))
    cases.append(("half of twenty-three min", True, 690, (), ((11.5, Scale(scale=60)),)))
    cases.append(("half twenty-three min", True, 690, (), ((11.5, Scale(scale=60)),)))

    cases.append(("half half twenty three min", False, 1380.0, (("half half", FailureFlags.AMBIGUOUS_MULTIPLIER),), ((23.0, Scale(scale=60.0)),)))
    cases.append(("half of half of twenty three min", False, 1380.0, (("half of half", FailureFlags.AMBIGUOUS_MULTIPLIER),), ((23.0, Scale(scale=60.0)),)))
    cases.append(("half of half twenty three min", False, 1380.0, (("half of half", FailureFlags.AMBIGUOUS_MULTIPLIER),), ((23.0, Scale(scale=60.0)),)))
    cases.append(("half half of twenty three min", False, 1380.0, (("half half", FailureFlags.AMBIGUOUS_MULTIPLIER),), ((23.0, Scale(scale=60.0)),)))
    cases.append(("twenty-three of half half mins", False, 0.0, (("twenty-three of half half", FailureFlags.AMBIGUOUS_MULTIPLIER), ("mins", FailureFlags.LONELY_SCALE)), ()))
    cases.append(("twenty-three half half of min", False, 0.0, (("twenty-three half half", FailureFlags.AMBIGUOUS_MULTIPLIER), ("min", FailureFlags.LONELY_SCALE)), ()))
    cases.append(("a million seconds half", False, 1000000.0, ((0.5, FailureFlags.LONELY_VALUE),), ((1000000.0, Scale(scale=1.0)),)))
    cases.append(("a million seconds half of", False, 1000000.0, (("of", FailureFlags.UNUSED_OPERATOR), (0.5, FailureFlags.LONELY_VALUE)), ((1000000.0, Scale(scale=1.0)),)))

    cases.append(("twenty-two sec", True, 22.0, (), ((22.0, Scale(scale=1.0)),)))
    cases.append(("thousand seconds", True, 1000.0, (), ((1000.0, Scale(scale=1.0)),)))
    cases.append(("a million seconds", True, 1000000.0, (), ((1000000.0, Scale(scale=1.0)),)))
    cases.append(("half a million seconds", True, 500000.0, (), ((500000.0, Scale(scale=1.0)),)))
    cases.append(("half million seconds", True, 500000.0, (), ((500000.0, Scale(scale=1.0)),)))
    cases.append(("third of a billion seconds", True, 333333333.3333333, (), ((333333333.3333333, Scale(scale=1.0)),)))
    cases.append(("one million half seconds", True, 500000.0, (), ((500000.0, Scale(scale=1.0)),)))
    cases.append(("one million of half seconds", True, 500000.0, (), ((500000.0, Scale(scale=1.0)),)))
    cases.append(("one half of minutes", True, 30.0, (), ((0.5, Scale(scale=60.0)),)))
    cases.append(("one half minutes of", False, 30.0, (("of", FailureFlags.UNUSED_OPERATOR),), ((0.5, Scale(scale=60.0)),)))
    cases.append(("the half of a million seconds", True, 500000.0, (), ((500000.0, Scale(scale=1.0)),)))
    cases.append(("twenty-five hundred minutes and half of one million two hundred and fifty-six thousand seconds", True, 778000.0, (), ((2500.0, Scale(scale=60.0)), (628000.0, Scale(scale=1.0)))))

    cases.append(("two of six minutes", True, 720.0, (), ((12.0, Scale(scale=60.0)),)))
    cases.append(("2 of six minutes", True, 720.0, (), ((12.0, Scale(scale=60.0)),)))
    cases.append(("two of 6 minutes", True, 720.0, (), ((12.0, Scale(scale=60.0)),)))
    cases.append(("2 of", False, 0.0, (("of", FailureFlags.UNUSED_OPERATOR), (2.0, FailureFlags.LONELY_VALUE)), ()))

    # Numeral Type Combinations + Float/Numeral Combinations
    cases.append(("FIVE hours, 2 minutes, 3s", True, 18123.0, (), ((5.0, Scale(scale=3600.0)), (2.0, Scale(scale=60.0)), (3.0, Scale(scale=1.0)))))
    cases.append(("1 2 seconds", False, 2.0, ((1.0, FailureFlags.LONELY_VALUE),), ((2.0, Scale(scale=1.0)),)))
    cases.append(("one two seconds", True, 12.0, (), ((12.0, Scale(scale=1.0)),)))
    cases.append(("1 two seconds", False, 2.0, ((1.0, FailureFlags.LONELY_VALUE),), ((2.0, Scale(scale=1.0)),)))
    cases.append(("one 2 seconds", False, 2.0, ((1.0, FailureFlags.LONELY_VALUE),), ((2.0, Scale(scale=1.0)),)))

    cases.append(("1 13 seconds", False, 13.0, ((1.0, FailureFlags.LONELY_VALUE),), ((13.0, Scale(scale=1.0)),)))
    cases.append(("one thirteen seconds", True, 113.0, (), ((113.0, Scale(scale=1.0)),)))
    cases.append(("1 thirteen seconds", False, 13.0, ((1.0, FailureFlags.LONELY_VALUE),), ((13.0, Scale(scale=1.0)),)))
    cases.append(("one 13 seconds", False, 13.0, ((1.0, FailureFlags.LONELY_VALUE),), ((13.0, Scale(scale=1.0)),)))

    cases.append(("1 50 seconds", False, 50.0, ((1.0, FailureFlags.LONELY_VALUE),), ((50.0, Scale(scale=1.0)),)))
    cases.append(("one fifty seconds", True, 150.0, (), ((150.0, Scale(scale=1.0)),)))
    cases.append(("1 fifty seconds", False, 50.0, ((1.0, FailureFlags.LONELY_VALUE),), ((50.0, Scale(scale=1.0)),)))
    cases.append(("one 50 seconds", False, 50.0, ((1.0, FailureFlags.LONELY_VALUE),), ((50.0, Scale(scale=1.0)),)))

    cases.append(("3 100 seconds", True, 3100.0, (), ((3100.0, Scale(scale=1.0)),)))
    cases.append(("three hundred seconds", True, 300.0, (), ((300.0, Scale(scale=1.0)),)))
    cases.append(("3 hundred seconds", True, 300.0, (), ((300.0, Scale(scale=1.0)),)))
    cases.append(("three 100 seconds", False, 100.0, ((3.0, FailureFlags.LONELY_VALUE),), ((100.0, Scale(scale=1.0)),)))
    cases.append(("three one hundred seconds", True, 3100.0, (), ((3100.0, Scale(scale=1.0)),)))
    cases.append(("three 1 hundred seconds", False, 100.0, ((3.0, FailureFlags.LONELY_VALUE),), ((100.0, Scale(scale=1.0)),)))
    cases.append(("3 one hundred seconds", False, 100.0, ((3.0, FailureFlags.LONELY_VALUE),), ((100.0, Scale(scale=1.0)),)))

    cases.append(("15 5 seconds", False, 5.0, ((15.0, FailureFlags.LONELY_VALUE),), ((5.0, Scale(scale=1.0)),)))
    cases.append(("fifteen five seconds", False, 5.0, ((15.0, FailureFlags.LONELY_VALUE),), ((5.0, Scale(scale=1.0)),)))
    cases.append(("15 five seconds", False, 5.0, ((15.0, FailureFlags.LONELY_VALUE),), ((5.0, Scale(scale=1.0)),)))
    cases.append(("fifteen 5 seconds", False, 5.0, ((15.0, FailureFlags.LONELY_VALUE),), ((5.0, Scale(scale=1.0)),)))

    cases.append(("15 15 seconds", False, 15.0, ((15.0, FailureFlags.LONELY_VALUE),), ((15.0, Scale(scale=1.0)),)))
    cases.append(("fifteen fifteen seconds", True, 1515.0, (), ((1515.0, Scale(scale=1.0)),)))
    cases.append(("15 fifteen seconds", False, 15.0, ((15.0, FailureFlags.LONELY_VALUE),), ((15.0, Scale(scale=1.0)),)))
    cases.append(("fifteen 15 seconds", False, 15.0, ((15.0, FailureFlags.LONELY_VALUE),), ((15.0, Scale(scale=1.0)),)))

    cases.append(("15 20 seconds", False, 20.0, ((15.0, FailureFlags.LONELY_VALUE),), ((20.0, Scale(scale=1.0)),)))
    cases.append(("fifteen twenty seconds", True, 1520.0, (), ((1520.0, Scale(scale=1.0)),)))
    cases.append(("15 twenty seconds", False, 20.0, ((15.0, FailureFlags.LONELY_VALUE),), ((20.0, Scale(scale=1.0)),)))
    cases.append(("fifteen 20 seconds", False, 20.0, ((15.0, FailureFlags.LONELY_VALUE),), ((20.0, Scale(scale=1.0)),)))

    cases.append(("20 1 seconds", False, 1.0, ((20.0, FailureFlags.LONELY_VALUE),), ((1.0, Scale(scale=1.0)),)))
    cases.append(("twenty one seconds", True, 21.0, (), ((21.0, Scale(scale=1.0)),)))
    cases.append(("20 one seconds", False, 1.0, ((20.0, FailureFlags.LONELY_VALUE),), ((1.0, Scale(scale=1.0)),)))
    cases.append(("twenty 1 seconds", False, 1.0, ((20.0, FailureFlags.LONELY_VALUE),), ((1.0, Scale(scale=1.0)),)))

    cases.append(("20 15 seconds", False, 15.0, ((20.0, FailureFlags.LONELY_VALUE),), ((15.0, Scale(scale=1.0)),)))
    cases.append(("twenty fifteen seconds", True, 2015.0, (), ((2015.0, Scale(scale=1.0)),)))
    cases.append(("20 fifteen seconds", False, 15.0, ((20.0, FailureFlags.LONELY_VALUE),), ((15.0, Scale(scale=1.0)),)))
    cases.append(("twenty 15 seconds", False, 15.0, ((20.0, FailureFlags.LONELY_VALUE),), ((15.0, Scale(scale=1.0)),)))

    cases.append(("20 30 seconds", False, 30.0, ((20.0, FailureFlags.LONELY_VALUE),), ((30.0, Scale(scale=1.0)),)))
    cases.append(("twenty thirty seconds", True, 2030.0, (), ((2030.0, Scale(scale=1.0)),)))
    cases.append(("20 thirty seconds", False, 30.0, ((20.0, FailureFlags.LONELY_VALUE),), ((30.0, Scale(scale=1.0)),)))
    cases.append(("twenty 30 seconds", False, 30.0, ((20.0, FailureFlags.LONELY_VALUE),), ((30.0, Scale(scale=1.0)),)))
    cases.append(("twenty twenty three seconds", True, 2023.0, (), ((30.0, Scale(scale=1.0)),)))
    cases.append(("twenty 20 three seconds", False, 3.0, ((20.0, FailureFlags.LONELY_VALUE), (20.0, FailureFlags.LONELY_VALUE)), ((3.0, Scale(scale=1.0)),)))
    cases.append(("twenty 20 3 seconds", False, 3.0, ((20.0, FailureFlags.LONELY_VALUE), (20.0, FailureFlags.LONELY_VALUE)), ((3.0, Scale(scale=1.0)),)))
    cases.append(("twenty 20 3", False, 0.0, ((20.0, FailureFlags.LONELY_VALUE), (20.0, FailureFlags.LONELY_VALUE), (3.0, FailureFlags.LONELY_VALUE)), ()))

    # Misc
    cases.append(("1 minute seconds", False, 60.0, (("seconds", FailureFlags.LONELY_SCALE),), ((1.0, Scale(scale=60.0)),)))
    cases.append(("minute 1 seconds", False, 1.0, (("minute", FailureFlags.LONELY_SCALE),), ((1.0, Scale(scale=1.0)),)))
    cases.append(("1, one 1", False, 0.0, ((1.0, FailureFlags.LONELY_VALUE), (1.0, FailureFlags.LONELY_VALUE), (1.0, FailureFlags.LONELY_VALUE)), ()))
    cases.append(("1!!!sec", False, 0.0, (("1!!!", FailureFlags.MISPLACED_ALLOWED_TERM), ("sec", FailureFlags.LONELY_SCALE)), ()))
    cases.append(("1, two/sec", False, 0.0, ((1.0, FailureFlags.LONELY_VALUE), (2.0, FailureFlags.LONELY_VALUE), ("/", FailureFlags.MISPLACED_SPECIAL), ("sec", FailureFlags.LONELY_SCALE)), ()))

    # Long Numerals + Segmentor Combinations
    cases.append(("twenty-three thousand sec", True, 23000.0, (), ((23000.0, Scale(scale=1.0)),)))
    cases.append(("two thousand twenty-three sec", True, 2023.0, (), ((30.0, Scale(scale=1.0)),)))
    cases.append(("two thousand twenty three five sec", False, 5.0, ((2023.0, FailureFlags.LONELY_VALUE),), ((5.0, Scale(scale=1.0)),)))
    cases.append(("two thousand twenty three thousand five sec", False, 23005.0, ((2000.0, FailureFlags.LONELY_VALUE),), ((23005.0, Scale(scale=1.0)),)))
    cases.append(("two thousand and twenty three five sec", False, 5.0, ((2023.0, FailureFlags.LONELY_VALUE),), ((5.0, Scale(scale=1.0)),)))
    cases.append(("one thousand five and hundred", True, 1500.0, (), ((1500.0, Scale(scale=1.0)),)))
    cases.append(("one thousand 5 and hundred", True, 1500.0, (), ((1500.0, Scale(scale=1.0)),)))

    cases.append(("one hundred seventy two thousand", True, 172000.0, (), ((172000.0, Scale(scale=1.0)),)))
    cases.append(("one hundred and seventy two thousand", True, 172000.0, (), ((172000.0, Scale(scale=1.0)),)))
    cases.append(("one million seventy two thousand", True, 1072000.0, (), ((1072000.0, Scale(scale=1.0)),)))
    cases.append(("one million and seventy two thousand", True, 1072000.0, (), ((1072000.0, Scale(scale=1.0)),)))
    cases.append(("one million seventy two thousand five hundred and six", True, 1072506.0, (), ((1072506.0, Scale(scale=1.0)),)))
    cases.append(("one million seventy and two thousand five hundred six", True, 1072506.0, (), ((1072506.0, Scale(scale=1.0)),)))
    cases.append(("one million seventy two thousand five hundred and six million", True, 1072506000000.0, (), ((1072506000000.0, Scale(scale=1.0)),)))
    cases.append(("one thousand six hundred     and five", False, 0.0, ((1600.0, FailureFlags.LONELY_VALUE), (" ", FailureFlags.CONSECUTIVE_CONNECTOR), (" ", FailureFlags.CONSECUTIVE_CONNECTOR), (" ", FailureFlags.CONSECUTIVE_CONNECTOR), (5.0, FailureFlags.LONELY_VALUE)), ()))
    cases.append(("five hundred and two hundred seconds", True, 700.0, (), ((700.0, Scale(scale=1.0)),)))
    cases.append(("one billion billion billion billion billion years", True, 3.1536000000000003e52, (), ((1.0000000000000001e45, Scale(scale=31536000.0)),)))

    # Awkward Thousands/Decimals
    cases.append(("twenty,18 three seconds", False, 3.0, ((20.0, FailureFlags.LONELY_VALUE), (18.0, FailureFlags.LONELY_VALUE)), ((3.0, Scale(scale=1.0)),)))
    cases.append(("twenty .18 three seconds", False, 3.0, ((20.0, FailureFlags.LONELY_VALUE), (0.18, FailureFlags.LONELY_VALUE)), ((3.0, Scale(scale=1.0)),)))
    cases.append(("twenty 18 three seconds", False, 3.0, ((20.0, FailureFlags.LONELY_VALUE), (18.0, FailureFlags.LONELY_VALUE)), ((3.0, Scale(scale=1.0)),)))

    # HHMMSS, Fractions, + Combinations
    cases.append(("12:30:15.25", True, 45015.25, (), ((12.0, Scale(scale=3600.0)), (30.0, Scale(scale=60.0)), (15.25, Scale(scale=1.0)))))
    cases.append(("22: 5", True, 1325.0, (), ((22.0, Scale(scale=60.0)), (5.0, Scale(scale=1.0)))))
    cases.append(("1:2:22:33 558:66:77.1234", True, 126558437.1234, (), ((1.0, Scale(scale=2635200.0)), (2.0, Scale(scale=604800.0)), (22.0, Scale(scale=86400.0)), (33558.0, Scale(scale=3600.0)), (66.0, Scale(scale=60.0)), (77.1234, Scale(scale=1.0)))))
    cases.append(("1 day 2:30:15.25", True, 95415.25, (), ((1.0, Scale(scale=86400.0)), (2.0, Scale(scale=3600.0)), (30.0, Scale(scale=60.0)), (15.25, Scale(scale=1.0)))))
    cases.append(("22: 2,455: 5555", True, 232055.0, (), ((22.0, Scale(scale=3600.0)), (2455.0, Scale(scale=60.0)), (5555.0, Scale(scale=1.0)))))
    cases.append(("22:  +2,455: 5555", False, 0.0, (("22:  +2,455: 5555", FailureFlags.MALFORMED_HHMMSS),), ()))
    cases.append(("22: 2,455 : 5555", False, 0.0, (("22: 2,455 : 5555", FailureFlags.MALFORMED_HHMMSS),), ()))
    cases.append(("22: 2,455 5: 5555", False, 3775.0, (("5: 5555", FailureFlags.DUPLICATE_SCALE),), ((22.0, Scale(scale=60.0)), (2455.0, Scale(scale=1.0)))))
    cases.append(("22: 2 455: +5555", True, 232055.0, (), ((22.0, Scale(scale=3600.0)), (2455.0, Scale(scale=60.0)), (5555.0, Scale(scale=1.0)))))
    cases.append(("22: 2,455: ++5555", False, 0.0, (("22: 2,455: ++5555", FailureFlags.MALFORMED_HHMMSS),), ()))
    cases.append(("2:55 5 minutes", False, 175.0, (("5 minutes", FailureFlags.DUPLICATE_SCALE),), ((2.0, Scale(scale=60.0)), (55.0, Scale(scale=1.0)))))
    cases.append(("2: 6 5: 2", False, 126.0, (("5: 2", FailureFlags.DUPLICATE_SCALE),), ((2.0, Scale(scale=60.0)), (6.0, Scale(scale=1.0)))))
    cases.append(("1/2 of a min", True, 30.0, (), ((0.5, Scale(scale=60.0)),)))
    cases.append(("1 / 2 of a min", True, 30.0, (), ((0.5, Scale(scale=60.0)),)))
    cases.append(("1+/+2 of a min", True, 30.0, (), ((0.5, Scale(scale=60.0)),)))
    cases.append(("+1 / +2 of a min", False, 60.0, (("1 / +2", FailureFlags.MALFORMED_FRACTION), ("of", FailureFlags.UNUSED_OPERATOR)), ((1.0, Scale(scale=60.0)),)))
    cases.append(("1 Day, 3:45:16.5", True, 99916.5, (), ((1.0, Scale(scale=86400.0)), (3.0, Scale(scale=3600.0)), (45.0, Scale(scale=60.0)), (16.5, Scale(scale=1.0)))))
    cases.append(("1:27/3:15.5:14", True, 119744.0, (), ((1.0, Scale(scale=86400.0)), (9.0, Scale(scale=3600.0)), (15.5, Scale(scale=60.0)), (14.0, Scale(scale=1.0)))))
    cases.append(("1+++/+++2 minutes", False, 0.0, (("1+++/+++2", FailureFlags.MALFORMED_FRACTION), ("minutes", FailureFlags.LONELY_SCALE)), ()))
    cases.append(("1+/+2 minutes", True, 30.0, (), ((0.5, Scale(scale=60.0)),)))
    cases.append(("1 / 2 / 3 minutes", False, 0.0, (("1 / 2 / 3", FailureFlags.MALFORMED_FRACTION), ("minutes", FailureFlags.LONELY_SCALE)), ()))
    cases.append(("1,2 /2..3 sec", False, 0.0, (("1,2 /2..3", FailureFlags.MALFORMED_DECIMAL | FailureFlags.MALFORMED_THOUSAND | FailureFlags.MALFORMED_FRACTION), ("sec", FailureFlags.LONELY_SCALE)), ()))
    cases.append(("1:1,2:1...4:6 sec", False, 0.0, (("1:1,2:1...4:6", FailureFlags.MALFORMED_DECIMAL | FailureFlags.MALFORMED_THOUSAND | FailureFlags.MALFORMED_HHMMSS), ("sec", FailureFlags.LONELY_SCALE)), ()))
    cases.append(("1/0 sec", False, 0.0, (("1/0", FailureFlags.MALFORMED_FRACTION), ("sec", FailureFlags.LONELY_SCALE)), ()))
    cases.append(("1:2::5", False, 0.0, (("1:2::5", FailureFlags.MALFORMED_HHMMSS),), ()))
    cases.append(("1:2/   3:1:5", False, 0.0, (("1:2/   3:1:5", FailureFlags.MALFORMED_FRACTION | FailureFlags.MALFORMED_HHMMSS),), ()))
    cases.append(("1:2:3:4:5:6:7:8:9:10:11", False, 0.0, (("1:2:3:4:5:6:7:8:9:10:11", FailureFlags.MALFORMED_HHMMSS),), ()))
    cases.append(("97 1:2:3", False, 3723.0, ((97.0, FailureFlags.LONELY_VALUE),), ((1.0, Scale(scale=3600.0)), (2.0, Scale(scale=60.0)), (3.0, Scale(scale=1.0)))))
    cases.append(("97, 5 1:2:3", False, 3723.0, ((97.0, FailureFlags.LONELY_VALUE), (5.0, FailureFlags.LONELY_VALUE)), ((1.0, Scale(scale=3600.0)), (2.0, Scale(scale=60.0)), (3.0, Scale(scale=1.0)))))
    cases.append(("97, half 5 1:2:3", False, 3723.0, ((97.0, FailureFlags.LONELY_VALUE), (0.5, FailureFlags.LONELY_VALUE), (5.0, FailureFlags.LONELY_VALUE)), ((1.0, Scale(scale=3600.0)), (2.0, Scale(scale=60.0)), (3.0, Scale(scale=1.0)))))

    # Duplicate Scales
    cases.append(("2 minutes and 3 minutes, 5 minutes", False, 120.0, (("3 minutes", FailureFlags.DUPLICATE_SCALE), ("5 minutes", FailureFlags.DUPLICATE_SCALE)), ((2.0, Scale(scale=60.0)),)))
    cases.append(("twenty hundred five seconds, twenty thousand seconds", False, 2005.0, (("twenty thousand seconds", FailureFlags.DUPLICATE_SCALE),), ((2005.0, Scale(scale=1.0)),)))
    cases.append(("twenty hundred five, twenty thousand seconds", False, 20000.0, ((2005.0, FailureFlags.LONELY_VALUE),), ((20000.0, Scale(scale=1.0)),)))

    return cases


def compare_scales(scale1: Scale, scale2: Scale) -> bool:
    """Compare two Scale objects based on the `scale` attribute."""
    return scale1.scale == scale2.scale


@pytest.mark.parametrize(
    "input, expected_success, expected_seconds, expected_invalid, expected_valid",
    generate_notstrict_tests(),
)
def test_notstrict_mode(
    tl_notstrict: TimeLength,
    input,
    expected_success,
    expected_seconds,
    expected_invalid,
    expected_valid,
):
    tl_notstrict.content = input
    tl_notstrict.parse()

    assert tl_notstrict.result.success == expected_success
    assert tl_notstrict.result.seconds == expected_seconds
    assert tl_notstrict.result.invalid == expected_invalid

    for actual_scale, expected_scale in zip(tl_notstrict.result.valid, expected_valid):
        assert compare_scales(actual_scale[1], expected_scale[1])


@pytest.mark.parametrize(
    "input, expected_success, expected_seconds, expected_invalid, expected_valid",
    generate_strict_tests(),
)
def test_strict_mode(
    tl_strict: TimeLength,
    input,
    expected_success,
    expected_seconds,
    expected_invalid,
    expected_valid,
):
    tl_strict.content = input
    tl_strict.parse()

    assert tl_strict.result.success == expected_success
    assert tl_strict.result.seconds == expected_seconds
    assert tl_strict.result.invalid == expected_invalid

    for actual_scale, expected_scale in zip(tl_strict.result.valid, expected_valid):
        assert compare_scales(actual_scale[1], expected_scale[1])


def generate_failureflag_tests():
    cases = []

    cases.append(("1 minute and 77 fake terms", True, FailureFlags.NONE, ParserSettings()))
    cases.append(("1. minutes", False, FailureFlags.MALFORMED_DECIMAL, ParserSettings(allow_decimals_lacking_digits=False)))
    cases.append(("1. minutes", True, FailureFlags.MALFORMED_DECIMAL, ParserSettings(allow_decimals_lacking_digits=True)))
    cases.append(("1,28 minutes", False, FailureFlags.MALFORMED_THOUSAND, ParserSettings(allow_thousands_lacking_digits=False, allow_thousands_extra_digits=True)))
    cases.append(("1,28 minutes", True, FailureFlags.MALFORMED_THOUSAND, ParserSettings(allow_thousands_lacking_digits=True, allow_thousands_extra_digits=True)))
    cases.append(("1,2897 seconds", False, FailureFlags.MALFORMED_THOUSAND, ParserSettings(allow_thousands_lacking_digits=True, allow_thousands_extra_digits=False)))
    cases.append(("1,2897 seconds", True, FailureFlags.MALFORMED_THOUSAND, ParserSettings(allow_thousands_lacking_digits=True, allow_thousands_extra_digits=True)))
    cases.append(("1  /  2 minutes", False, FailureFlags.MALFORMED_FRACTION, ParserSettings()))
    cases.append(("1:   2:   3", False, FailureFlags.MALFORMED_HHMMSS, ParserSettings()))
    cases.append(("1s 2", False, FailureFlags.LONELY_VALUE, ParserSettings()))
    cases.append(("1 2s", False, FailureFlags.LONELY_VALUE, ParserSettings()))
    cases.append(("minutes 1s", False, FailureFlags.LONELY_SCALE, ParserSettings()))
    cases.append(("1s 2s", False, FailureFlags.DUPLICATE_SCALE, ParserSettings(allow_duplicate_scales=False)))
    cases.append(("1s 2s", True, FailureFlags.DUPLICATE_SCALE, ParserSettings(allow_duplicate_scales=True)))
    cases.append(("1s s", False, FailureFlags.LONELY_SCALE, ParserSettings()))
    # 2 connectors are allowed in a row, so test for 3.
    cases.append(("1   2 minutes", False, FailureFlags.CONSECUTIVE_CONNECTOR, ParserSettings()))
    cases.append(("1,,2 minutes", False, FailureFlags.CONSECUTIVE_SEGMENTOR, ParserSettings()))
    cases.append(("1 min!!", False, FailureFlags.CONSECUTIVE_SPECIAL, ParserSettings()))
    cases.append(("1!min", False, FailureFlags.MISPLACED_ALLOWED_TERM, ParserSettings(limit_allowed_terms=True)))
    cases.append(("1!min", True, FailureFlags.MISPLACED_ALLOWED_TERM, ParserSettings(limit_allowed_terms=False)))
    cases.append(("1, /2", False, FailureFlags.MISPLACED_SPECIAL, ParserSettings()))
    cases.append(("1 min of", False, FailureFlags.UNUSED_OPERATOR, ParserSettings()))
    cases.append(("half of a quarter of 5 minutes", False, FailureFlags.AMBIGUOUS_MULTIPLIER, ParserSettings()))

    cases.append(("1 minute and 77 fake terms", False, FailureFlags.ALL, ParserSettings()))
    cases.append(("1. minutes", False, FailureFlags.ALL, ParserSettings(allow_decimals_lacking_digits=False)))
    cases.append(("1. minutes", True, FailureFlags.ALL, ParserSettings(allow_decimals_lacking_digits=True)))
    cases.append(("1,28 minutes", False, FailureFlags.ALL, ParserSettings(allow_thousands_lacking_digits=False, allow_thousands_extra_digits=True)))
    cases.append(("1,28 minutes", True, FailureFlags.ALL, ParserSettings(allow_thousands_lacking_digits=True, allow_thousands_extra_digits=True)))
    cases.append(("1,2897 seconds", False, FailureFlags.ALL, ParserSettings(allow_thousands_lacking_digits=True, allow_thousands_extra_digits=False)))
    cases.append(("1,2897 seconds", True, FailureFlags.ALL, ParserSettings(allow_thousands_lacking_digits=True, allow_thousands_extra_digits=True)))
    cases.append(("1  /  2 minutes", False, FailureFlags.ALL, ParserSettings()))
    cases.append(("1:   2:   3", False, FailureFlags.ALL, ParserSettings()))
    cases.append(("1s 2", False, FailureFlags.ALL, ParserSettings()))
    cases.append(("1 2s", False, FailureFlags.ALL, ParserSettings()))
    cases.append(("minutes 1s", False, FailureFlags.ALL, ParserSettings()))
    cases.append(("1s 2s", False, FailureFlags.ALL, ParserSettings(allow_duplicate_scales=False)))
    cases.append(("1s 2s", True, FailureFlags.ALL, ParserSettings(allow_duplicate_scales=True)))
    cases.append(("1s s", False, FailureFlags.ALL, ParserSettings()))
    # 2 connectors are allowed in a row, so test for 3.
    cases.append(("1   2 minutes", False, FailureFlags.ALL, ParserSettings()))
    cases.append(("1,,2 minutes", False, FailureFlags.ALL, ParserSettings()))
    cases.append(("1 min!!", False, FailureFlags.ALL, ParserSettings()))
    cases.append(("1!min", False, FailureFlags.ALL, ParserSettings(limit_allowed_terms=True)))
    cases.append(("1!min", True, FailureFlags.ALL, ParserSettings(limit_allowed_terms=False)))
    cases.append(("1, /2", False, FailureFlags.ALL, ParserSettings()))
    cases.append(("1 min of", False, FailureFlags.ALL, ParserSettings()))
    cases.append(("half of a quarter of 5 minutes", False, FailureFlags.ALL, ParserSettings()))

    return cases


def extract_failureflags(tl: TimeLength) -> FailureFlags:
    combined_flags = FailureFlags.NONE

    for item in tl.result.invalid:
        combined_flags |= item[1]

    return combined_flags


@pytest.mark.parametrize(
    "input, expected_success, failureflag, parsersettings",
    generate_failureflag_tests(),
)
def test_failureflags(
    tl_notstrict: TimeLength,
    input,
    expected_success,
    failureflag,
    parsersettings,
):
    tl_notstrict.content = input
    tl_notstrict.locale.flags = failureflag
    tl_notstrict.locale.settings = parsersettings
    tl_notstrict.parse()

    assert tl_notstrict.result.success == expected_success
    assert (failureflag == FailureFlags.NONE and tl_notstrict.result.success) or (not tl_notstrict.result.success and (extract_failureflags(tl_notstrict) & failureflag)) or (tl_notstrict.result.success and not (extract_failureflags(tl_notstrict) & failureflag))
