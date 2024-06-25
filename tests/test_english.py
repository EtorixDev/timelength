import pytest

from timelength.locales import English
from timelength.timelength import TimeLength
from timelength.dataclasses import Scale


@pytest.fixture
def tl_notstrict():
    return TimeLength(content = "0 seconds", strict = False, locale = English())


@pytest.fixture
def tl_strict():
    return TimeLength(content = "0 seconds", strict = True, locale = English())


def generate_notstrict_tests():
    cases = []
    # Basic Functionality
    cases.append(("", False, 0.0, [], [],))
    cases.append(("AHHHHH, what???###", False, 0.0, [("AHHHHH", "UNKNOWN_TERM"), ("what", "UNKNOWN_TERM"), ("###", "UNKNOWN_TERM"), ("?", "CONSECUTIVE_SPECIALS"), ("?", "CONSECUTIVE_SPECIALS")], [],))
    cases.append(("0", True, 0.0, [], [(0.0, Scale(scale = 1.0))],))
    cases.append(("5 seconds", True, 5.0, [], [(5.0, Scale(scale = 1.0))],))
    cases.append(("5 seconds 3", True, 5.0, [(3.0, "LONELY_VALUE")], [(5.0, Scale(scale = 1.0))],))
    for decimal in English()._decimal_separators:
        cases.append((f"5{decimal}5 seconds", True, 5.5, [], [(5.5, Scale(scale = 1.0))],))
    for thousand in English()._thousand_separators:
        cases.append((f"5{thousand}500 seconds", True, 5500.0, [], [(5500.0, Scale(scale = 1.0))],))
    for thousand in English()._thousand_separators:
        for decimal in English()._decimal_separators:
            cases.append((f"5{thousand}500{decimal}55 seconds", True, 5500.55, [], [(5500.55, Scale(scale = 1.0))],))
    cases.append(("1h5m30s", True, 3930.0, [], [(1.0, Scale(scale = 3600.0)), (5.0, Scale(scale = 60.0)), (30.0, Scale(scale = 1.0))],))
    cases.append(("1 hour 5 minutes 30 seconds", True, 3930.0, [], [(1.0, Scale(scale = 3600.0)), (5.0, Scale(scale = 60.0)), (30.0, Scale(scale = 1.0))],))
    cases.append(("1 hour 5min30s", True, 3930.0, [], [(1.0, Scale(scale = 3600.0)), (5.0, Scale(scale = 60.0)), (30.0, Scale(scale = 1.0))],))

    # Segmentors as of Writing: "," "and" "&"
    cases.append(("1 hour, 5 minutes, and 30 seconds & 7ms", True, 3930.007, [], [(1.0, Scale(scale = 3600.0)), (5.0, Scale(scale = 60.0)), (30.0, Scale(scale = 1.0)), (7.0, Scale(scale = 0.001))],))
    cases.append(("5m,, 5s", True, 305.0, [(",", "CONSECUTIVE_SPECIALS")], [(5.0, Scale(scale = 60.0)), (5.0, Scale(scale = 1.0))],))
    cases.append(("1, 2, 3 minutes", True, 360.0, [], [(6.0, Scale(scale = 60.0))],))
    # Connectors as of Writing: " ", "-", "\t"
    cases.append(("1 minute-2-seconds	3MS", True, 62.003, [], [(1.0, Scale(scale = 60.0)), (2.0, Scale(scale = 1.0)), (3.0, Scale(scale = 0.001))],))

    # Numerals / Modifiers / Multipliers
    cases.append(("zero", True, 0.0, [], [(0.0, Scale(scale = 1.0))],))
    cases.append(("zero minutes", True, 0.0, [], [(0.0, Scale(scale = 60.0))],))
    cases.append(("five", True, 5.0, [], [(5.0, Scale(scale = 1.0))],))
    
    cases.append(("one thousand", True, 1000.0, [], [],))
    cases.append(("one thousand and five", True, 1005.0, [], [],))
    cases.append(("one thousand seconds and five", True, 1000.0, [(5.0, "LONELY_VALUE")], [],))

    cases.append(("twenty-two sec", True, 22.0, [], [(22.0, Scale(scale = 1.0))],))
    cases.append(("thousand seconds", True, 1000.0, [], [(1000.0, Scale(scale = 1.0))],))
    cases.append(("a million seconds", True, 1000000.0, [], [(1000000.0, Scale(scale = 1.0))],))
    cases.append(("half a million seconds", True, 500000.0, [], [(500000.0, Scale(scale = 1.0))],))
    cases.append(("third of a billion seconds", True, 333333333.3333333, [], [(333333333.3333333, Scale(scale = 1.0))],))
    cases.append(("one million half seconds", True, 500000.0, [], [(500000.0, Scale(scale = 1.0))],))
    cases.append(("one million of half seconds", True, 500000.0, [], [(500000.0, Scale(scale = 1.0))],))
    cases.append(("one half of minutes", True, 30.0, [], [(0.5, Scale(scale = 60.0))],))
    cases.append(("one half minutes of", True, 30.0, [("of", "UNUSED_MULTIPLIER")], [(0.5, Scale(scale = 60.0))],))
    cases.append(("the half of a million seconds", True, 500000.0, [], [(500000.0, Scale(1.0, "segundo", "segundos"))],))
    
    for item in English()._numerals["multiplier"]["terms"]:
        cases.append((f"two {item} six minutes", True, 720.0, [], [(12.0, Scale(scale = 60.0))],))
    for item in English()._numerals["multiplier"]["terms"]:
        cases.append((f"2 {item} six minutes", True, 720.0, [], [(12.0, Scale(scale = 60.0))],))
    for item in English()._numerals["multiplier"]["terms"]:
        cases.append((f"two {item} 6 minutes", True, 720.0, [], [(12.0, Scale(scale = 60.0))],))
    for item in English()._numerals["multiplier"]["terms"]:
        cases.append((f"2 {item}", False, 0.0, [(f"{item}", "UNUSED_MULTIPLIER"), (2.0, "LONELY_VALUE")], [],))

    # Numeral Type Combinations + Float/Numeral Combinations
    cases.append(("FIVE hours, 2 minutes, 3s", True, 18123.0, [], [(5.0, Scale(scale = 3600.0)), (2.0, Scale(scale = 60.0)), (3.0, Scale(scale = 1.0))],))
    cases.append(("1 2 seconds", True, 2.0, [(1.0, "CONSECUTIVE_VALUES")], [(2.0, Scale(scale = 1.0))],))
    cases.append(("one two seconds", True, 12.0, [], [(12.0, Scale(scale = 1.0))],))
    cases.append(("1 two seconds", True, 2.0, [(1.0, "CONSECUTIVE_VALUES")], [(2.0, Scale(scale = 1.0))],))
    cases.append(("one 2 seconds", True, 2.0, [(1.0, "CONSECUTIVE_VALUES")], [(2.0, Scale(scale = 1.0))],))

    cases.append(("1 13 seconds", True, 13.0, [(1.0, "CONSECUTIVE_VALUES")], [(13.0, Scale(scale = 1.0))],))
    cases.append(("one thirteen seconds", True, 113.0, [], [(113.0, Scale(scale = 1.0))],))
    cases.append(("1 thirteen seconds", True, 13.0, [(1.0, "CONSECUTIVE_VALUES")], [(13.0, Scale(scale = 1.0))],))
    cases.append(("one 13 seconds", True, 13.0, [(1.0, "CONSECUTIVE_VALUES")], [(13.0, Scale(scale = 1.0))],))

    cases.append(("1 50 seconds", True, 50.0, [(1.0, "CONSECUTIVE_VALUES")], [(50.0, Scale(scale = 1.0))],))
    cases.append(("one fifty seconds", True, 150.0, [], [(150.0, Scale(scale = 1.0))],))
    cases.append(("1 fifty seconds", True, 50.0, [(1.0, "CONSECUTIVE_VALUES")], [(50.0, Scale(scale = 1.0))],))
    cases.append(("one 50 seconds", True, 50.0, [(1.0, "CONSECUTIVE_VALUES")], [(50.0, Scale(scale = 1.0))],))

    cases.append(("3 100 seconds", True, 3100.0, [], [(3100.0, Scale(scale = 1.0))],))
    cases.append(("three hundred seconds", True, 300.0, [], [(300.0, Scale(scale = 1.0))],))
    cases.append(("3 hundred seconds", True, 300.0, [], [(300.0, Scale(scale = 1.0))],))
    cases.append(("three 100 seconds", True, 100.0, [(3.0, "CONSECUTIVE_VALUES")], [(100.0, Scale(scale = 1.0))],))
    cases.append(("three one hundred seconds", True, 3100.0, [], [(3100.0, Scale(scale = 1.0))],))
    cases.append(("three 1 hundred seconds", True, 100.0, [(3.0, "CONSECUTIVE_VALUES")], [(100.0, Scale(scale = 1.0))],))
    cases.append(("3 one hundred seconds", True, 100.0, [(3.0, "CONSECUTIVE_VALUES")], [(100.0, Scale(scale = 1.0))],))

    cases.append(("15 5 seconds", True, 5.0, [(15.0, "CONSECUTIVE_VALUES")], [(5.0, Scale(scale = 1.0))],))
    cases.append(("fifteen five seconds", True, 5.0, [(15.0, "CONSECUTIVE_VALUES")], [(5.0, Scale(scale = 1.0))],))
    cases.append(("15 five seconds", True, 5.0, [(15.0, "CONSECUTIVE_VALUES")], [(5.0, Scale(scale = 1.0))],))
    cases.append(("fifteen 5 seconds", True, 5.0, [(15.0, "CONSECUTIVE_VALUES")], [(5.0, Scale(scale = 1.0))],))

    cases.append(("15 15 seconds", True, 15.0, [(15.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale = 1.0))],))
    cases.append(("fifteen fifteen seconds", True, 1515.0, [], [(1515.0, Scale(scale = 1.0))],))
    cases.append(("15 fifteen seconds", True, 15.0, [(15.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale = 1.0))],))
    cases.append(("fifteen 15 seconds", True, 15.0, [(15.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale = 1.0))],))

    cases.append(("15 20 seconds", True, 20.0, [(15.0, "CONSECUTIVE_VALUES")], [(20.0, Scale(scale = 1.0))],))
    cases.append(("fifteen twenty seconds", True, 1520.0, [], [(1520.0, Scale(scale = 1.0))],))
    cases.append(("15 twenty seconds", True, 20.0, [(15.0, "CONSECUTIVE_VALUES")], [(20.0, Scale(scale = 1.0))],))
    cases.append(("fifteen 20 seconds", True, 20.0, [(15.0, "CONSECUTIVE_VALUES")], [(20.0, Scale(scale = 1.0))],))

    cases.append(("20 1 seconds", True, 1.0, [(20.0, "CONSECUTIVE_VALUES")], [(1.0, Scale(scale = 1.0))],))
    cases.append(("twenty one seconds", True, 21.0, [], [(21.0, Scale(scale = 1.0))],))
    cases.append(("20 one seconds", True, 1.0, [(20.0, "CONSECUTIVE_VALUES")], [(1.0, Scale(scale = 1.0))],))
    cases.append(("twenty 1 seconds", True, 1.0, [(20.0, "CONSECUTIVE_VALUES")], [(1.0, Scale(scale = 1.0))],))

    cases.append(("20 15 seconds", True, 15.0, [(20.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale = 1.0))],))
    cases.append(("twenty fifteen seconds", True, 2015.0, [], [(2015.0, Scale(scale = 1.0))],))
    cases.append(("20 fifteen seconds", True, 15.0, [(20.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale = 1.0))],))
    cases.append(("twenty 15 seconds", True, 15.0, [(20.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale = 1.0))],))

    cases.append(("20 30 seconds", True, 30.0, [(20.0, "CONSECUTIVE_VALUES")], [(30.0, Scale(scale = 1.0))],))
    cases.append(("twenty thirty seconds", True, 2030.0, [], [(2030.0, Scale(scale = 1.0))],))
    cases.append(("20 thirty seconds", True, 30.0, [(20.0, "CONSECUTIVE_VALUES")], [(30.0, Scale(scale = 1.0))],))
    cases.append(("twenty 30 seconds", True, 30.0, [(20.0, "CONSECUTIVE_VALUES")], [(30.0, Scale(scale = 1.0))],))

    cases.append(("twenty-three thousand sec", True, 23000.0, [], [(23000.0, Scale(scale = 1.0))],))
    cases.append(("two thousand twenty-three sec", True, 2023.0, [], [(30.0, Scale(scale = 1.0))],))
    cases.append(("two thousand twenty three five sec", True, 5.0, [(2023.0, 'CONSECUTIVE_VALUES')], [(5.0, Scale(scale = 1.0))],))
    cases.append(("two thousand twenty three thousand five sec", True, 23005.0, [(2000.0, 'LONELY_VALUE')], [(23005.0, Scale(scale = 1.0))],))
    cases.append(("two thousand and twenty three five sec", True, 5.0, [(2023.0, 'CONSECUTIVE_VALUES')], [(5.0, Scale(scale = 1.0))],))
    
    cases.append(("one hundred seventy two thousand", True, 172000.0, [], [(172000.0, Scale(scale = 1.0))],))
    cases.append(("one hundred and seventy two thousand", True, 172000.0, [], [(172000.0, Scale(scale = 1.0))],))
    cases.append(("one million seventy two thousand", True, 1072000.0, [], [(1072000.0, Scale(scale = 1.0))],))
    cases.append(("one million and seventy two thousand", True, 1072000.0, [], [(1072000.0, Scale(scale = 1.0))],))
    cases.append(("one million seventy two thousand five hundred and six", True, 1072506.0, [], [(1072506.0, Scale(scale = 1.0))],))
    cases.append(("one million seventy two thousand five hundred and six million", True, 1072506000000.0, [], [(1072506000000.0, Scale(scale = 1.0))],))

    cases.append(("twenty twenty three seconds", True, 2023.0, [], [(2023.0, Scale(scale = 1.0))],))
    cases.append(("twenty 20 three seconds", True, 3.0, [(20.0, "CONSECUTIVE_VALUES"), (20.0, "CONSECUTIVE_VALUES")], [(3.0, Scale(scale = 1.0))],))
    cases.append(("twenty 20 3 seconds", True, 3.0, [(20.0, "CONSECUTIVE_VALUES"), (20.0, "CONSECUTIVE_VALUES")], [(3.0, Scale(scale = 1.0))],))
    cases.append(("twenty 20 3", False, 0.0, [(20.0, "CONSECUTIVE_VALUES"), (20.0, "CONSECUTIVE_VALUES"), (3.0, "LONELY_VALUE"),], [],))
    cases.append(("twenty,18 three seconds", True, 3.0, [(20.0, "CONSECUTIVE_VALUES"), (18.0, "CONSECUTIVE_VALUES")], [(3.0, Scale(scale = 1.0))],))
    cases.append(("twenty 18 three seconds", True, 3.0, [(20.0, "CONSECUTIVE_VALUES"), (18.0, "CONSECUTIVE_VALUES")], [(3.0, Scale(scale = 1.0))],))

    cases.append(("1 minute seconds", True, 60.0, [("seconds", "CONSECUTIVE_SCALES")], [(1.0, Scale(scale = 60.0))],))
    cases.append(("minute 1 seconds", True, 1.0, [("minute", "LEADING_SCALE")], [(1.0, Scale(scale = 1.0))],))
    return cases


def generate_strict_tests():
    cases = []
    # Basic Functionality
    cases.append(("", False, 0.0, [], [],))
    cases.append(("AHHHHH, what???###", False, 0.0, [("AHHHHH", "UNKNOWN_TERM"), ("what", "UNKNOWN_TERM"), ("###", "UNKNOWN_TERM"), ("?", "CONSECUTIVE_SPECIALS"), ("?", "CONSECUTIVE_SPECIALS")], [],))
    cases.append(("0", False, 0.0, [(0.0, "LONELY_VALUE")], [],))
    cases.append(("5 seconds", True, 5.0, [], [(5.0, Scale(scale = 1.0))],))
    cases.append(("5 seconds 3", False, 5.0, [(3.0, "LONELY_VALUE")], [(5.0, Scale(scale = 1.0))],))
    for decimal in English()._decimal_separators:
        cases.append((f"5{decimal}5 seconds", True, 5.5, [], [(5.5, Scale(scale = 1.0))],))
    for thousand in English()._thousand_separators:
        cases.append((f"5{thousand}500 seconds", True, 5500.0, [], [(5500.0, Scale(scale = 1.0))],))
    for thousand in English()._thousand_separators:
        for decimal in English()._decimal_separators:
            cases.append((f"5{thousand}500{decimal}55 seconds", True, 5500.55, [], [(5500.55, Scale(scale = 1.0))],))
    cases.append(("1h5m30s", True, 3930.0, [], [(1.0, Scale(scale = 3600.0)), (5.0, Scale(scale = 60.0)), (30.0, Scale(scale = 1.0))],))
    cases.append(("1 hour 5 minutes 30 seconds", True, 3930.0, [], [(1.0, Scale(scale = 3600.0)), (5.0, Scale(scale = 60.0)), (30.0, Scale(scale = 1.0))],))
    cases.append(("1 hour 5min30s", True, 3930.0, [], [(1.0, Scale(scale = 3600.0)), (5.0, Scale(scale = 60.0)), (30.0, Scale(scale = 1.0))],))

    # Segmentors as of Writing: "," "and" "&"
    cases.append(("1 hour, 5 minutes, and 30 seconds & 7ms", True, 3930.007, [], [(1.0, Scale(scale = 3600.0)), (5.0, Scale(scale = 60.0)), (30.0, Scale(scale = 1.0)), (7.0, Scale(scale = 0.001))],))
    cases.append(("5m,, 5s", False, 305.0, [(",", "CONSECUTIVE_SPECIALS")], [(5.0, Scale(scale = 60.0)), (5.0, Scale(scale = 1.0))],))
    cases.append(("1, 2, 3 minutes", True, 360.0, [], [(6.0, Scale(scale = 60.0))],))
    # Connectors as of Writing: " ", "-", "\t"
    cases.append(("1 minute-2-seconds	3MS", True, 62.003, [], [(1.0, Scale(scale = 60.0)), (2.0, Scale(scale = 1.0)), (3.0, Scale(scale = 0.001))],))

    # Numerals / Modifiers / Multipliers
    cases.append(("zero", False, 0.0, [(0.0, "LONELY_VALUE")], [],))
    cases.append(("zero minutes", True, 0.0, [], [(0.0, Scale(scale = 60.0))],))
    cases.append(("five", False, 0.0, [(5.0, "LONELY_VALUE")], [],))
    
    cases.append(("one thousand", False, 0.0, [(1000.0, "LONELY_VALUE")], [],))
    cases.append(("one thousand and five", False, 0, [(1005.0, "LONELY_VALUE")], [],))
    cases.append(("one thousand seconds and five", False, 1000.0, [(5.0, "LONELY_VALUE")], [],))

    cases.append(("twenty-two sec", True, 22.0, [], [(22.0, Scale(scale = 1.0))],))
    cases.append(("thousand seconds", True, 1000.0, [], [(1000.0, Scale(scale = 1.0))],))
    cases.append(("a million seconds", True, 1000000.0, [], [(1000000.0, Scale(scale = 1.0))],))
    cases.append(("half a million seconds", True, 500000.0, [], [(500000.0, Scale(scale = 1.0))],))
    cases.append(("third of a billion seconds", True, 333333333.3333333, [], [(333333333.3333333, Scale(scale = 1.0))],))
    cases.append(("one million half seconds", True, 500000.0, [], [(500000.0, Scale(scale = 1.0))],))
    cases.append(("one million of half seconds", True, 500000.0, [], [(500000.0, Scale(scale = 1.0))],))
    cases.append(("one half of minutes", True, 30.0, [], [(0.5, Scale(scale = 60.0))],))
    cases.append(("one half minutes of", False, 30.0, [("of", "UNUSED_MULTIPLIER")], [(0.5, Scale(scale = 60.0))],))
    cases.append(("the half of a million seconds", True, 500000.0, [], [(500000.0, Scale(1.0, "segundo", "segundos"))],))

    for item in English()._numerals["multiplier"]["terms"]:
        cases.append((f"two {item} six minutes", True, 720.0, [], [(12.0, Scale(scale = 60.0))],))
    for item in English()._numerals["multiplier"]["terms"]:
        cases.append((f"2 {item} six minutes", True, 720.0, [], [(12.0, Scale(scale = 60.0))],))
    for item in English()._numerals["multiplier"]["terms"]:
        cases.append((f"two {item} 6 minutes", True, 720.0, [], [(12.0, Scale(scale = 60.0))],))
    for item in English()._numerals["multiplier"]["terms"]:
        cases.append((f"2 {item}", False, 0.0, [(f"{item}", "UNUSED_MULTIPLIER"), (2.0, "LONELY_VALUE")], [],))

    # Numeral Type Combinations + Float/Numeral Combinations
    cases.append(("FIVE hours, 2 minutes, 3s", True, 18123.0, [], [(5.0, Scale(scale = 3600.0)), (2.0, Scale(scale = 60.0)), (3.0, Scale(scale = 1.0))],))
    cases.append(("1 2 seconds", False, 2.0, [(1.0, "CONSECUTIVE_VALUES")], [(2.0, Scale(scale = 1.0))],))
    cases.append(("one two seconds", True, 12.0, [], [(12.0, Scale(scale = 1.0))],))
    cases.append(("1 two seconds", False, 2.0, [(1.0, "CONSECUTIVE_VALUES")], [(2.0, Scale(scale = 1.0))],))
    cases.append(("one 2 seconds", False, 2.0, [(1.0, "CONSECUTIVE_VALUES")], [(2.0, Scale(scale = 1.0))],))

    cases.append(("1 13 seconds", False, 13.0, [(1.0, "CONSECUTIVE_VALUES")], [(13.0, Scale(scale = 1.0))],))
    cases.append(("one thirteen seconds", True, 113.0, [], [(113.0, Scale(scale = 1.0))],))
    cases.append(("1 thirteen seconds", False, 13.0, [(1.0, "CONSECUTIVE_VALUES")], [(13.0, Scale(scale = 1.0))],))
    cases.append(("one 13 seconds", False, 13.0, [(1.0, "CONSECUTIVE_VALUES")], [(13.0, Scale(scale = 1.0))],))

    cases.append(("1 50 seconds", False, 50.0, [(1.0, "CONSECUTIVE_VALUES")], [(50.0, Scale(scale = 1.0))],))
    cases.append(("one fifty seconds", True, 150.0, [], [(150.0, Scale(scale = 1.0))],))
    cases.append(("1 fifty seconds", False, 50.0, [(1.0, "CONSECUTIVE_VALUES")], [(50.0, Scale(scale = 1.0))],))
    cases.append(("one 50 seconds", False, 50.0, [(1.0, "CONSECUTIVE_VALUES")], [(50.0, Scale(scale = 1.0))],))

    cases.append(("3 100 seconds", True, 3100.0, [], [(3100.0, Scale(scale = 1.0))],))
    cases.append(("three hundred seconds", True, 300.0, [], [(300.0, Scale(scale = 1.0))],))
    cases.append(("3 hundred seconds", True, 300.0, [], [(300.0, Scale(scale = 1.0))],))
    cases.append(("three 100 seconds", False, 100.0, [(3.0, "CONSECUTIVE_VALUES")], [(100.0, Scale(scale = 1.0))],))
    cases.append(("three one hundred seconds", True, 3100.0, [], [(3100.0, Scale(scale = 1.0))],))
    cases.append(("three 1 hundred seconds", False, 100.0, [(3.0, "CONSECUTIVE_VALUES")], [(100.0, Scale(scale = 1.0))],))
    cases.append(("3 one hundred seconds", False, 100.0, [(3.0, "CONSECUTIVE_VALUES")], [(100.0, Scale(scale = 1.0))],))

    cases.append(("15 5 seconds", False, 5.0, [(15.0, "CONSECUTIVE_VALUES")], [(5.0, Scale(scale = 1.0))],))
    cases.append(("fifteen five seconds", False, 5.0, [(15.0, "CONSECUTIVE_VALUES")], [(5.0, Scale(scale = 1.0))],))
    cases.append(("15 five seconds", False, 5.0, [(15.0, "CONSECUTIVE_VALUES")], [(5.0, Scale(scale = 1.0))],))
    cases.append(("fifteen 5 seconds", False, 5.0, [(15.0, "CONSECUTIVE_VALUES")], [(5.0, Scale(scale = 1.0))],))

    cases.append(("15 15 seconds", False, 15.0, [(15.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale = 1.0))],))
    cases.append(("fifteen fifteen seconds", True, 1515.0, [], [(1515.0, Scale(scale = 1.0))],))
    cases.append(("15 fifteen seconds", False, 15.0, [(15.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale = 1.0))],))
    cases.append(("fifteen 15 seconds", False, 15.0, [(15.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale = 1.0))],))

    cases.append(("15 20 seconds", False, 20.0, [(15.0, "CONSECUTIVE_VALUES")], [(20.0, Scale(scale = 1.0))],))
    cases.append(("fifteen twenty seconds", True, 1520.0, [], [(1520.0, Scale(scale = 1.0))],))
    cases.append(("15 twenty seconds", False, 20.0, [(15.0, "CONSECUTIVE_VALUES")], [(20.0, Scale(scale = 1.0))],))
    cases.append(("fifteen 20 seconds", False, 20.0, [(15.0, "CONSECUTIVE_VALUES")], [(20.0, Scale(scale = 1.0))],))

    cases.append(("20 1 seconds", False, 1.0, [(20.0, "CONSECUTIVE_VALUES")], [(1.0, Scale(scale = 1.0))],))
    cases.append(("twenty one seconds", True, 21.0, [], [(21.0, Scale(scale = 1.0))],))
    cases.append(("20 one seconds", False, 1.0, [(20.0, "CONSECUTIVE_VALUES")], [(1.0, Scale(scale = 1.0))],))
    cases.append(("twenty 1 seconds", False, 1.0, [(20.0, "CONSECUTIVE_VALUES")], [(1.0, Scale(scale = 1.0))],))

    cases.append(("20 15 seconds", False, 15.0, [(20.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale = 1.0))],))
    cases.append(("twenty fifteen seconds", True, 2015.0, [], [(2015.0, Scale(scale = 1.0))],))
    cases.append(("20 fifteen seconds", False, 15.0, [(20.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale = 1.0))],))
    cases.append(("twenty 15 seconds", False, 15.0, [(20.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale = 1.0))],))

    cases.append(("20 30 seconds", False, 30.0, [(20.0, "CONSECUTIVE_VALUES")], [(30.0, Scale(scale = 1.0))],))
    cases.append(("twenty thirty seconds", True, 2030.0, [], [(2030.0, Scale(scale = 1.0))],))
    cases.append(("20 thirty seconds", False, 30.0, [(20.0, "CONSECUTIVE_VALUES")], [(30.0, Scale(scale = 1.0))],))
    cases.append(("twenty 30 seconds", False, 30.0, [(20.0, "CONSECUTIVE_VALUES")], [(30.0, Scale(scale = 1.0))],))

    cases.append(("twenty-three thousand sec", True, 23000.0, [], [(23000.0, Scale(scale = 1.0))],))
    cases.append(("two thousand twenty-three sec", True, 2023.0, [], [(30.0, Scale(scale = 1.0))],))
    cases.append(("two thousand twenty three five sec", False, 5.0, [(2023.0, 'CONSECUTIVE_VALUES')], [(5.0, Scale(scale = 1.0))],))
    cases.append(("two thousand twenty three thousand five sec", False, 23005.0, [(2000.0, 'LONELY_VALUE')], [(23005.0, Scale(scale = 1.0))],))
    cases.append(("two thousand and twenty three five sec", False, 5.0, [(2023.0, 'CONSECUTIVE_VALUES')], [(5.0, Scale(scale = 1.0))],))
    
    cases.append(("one hundred seventy two thousand", False, 0.0, [(172000.0, 'LONELY_VALUE')], [],))
    cases.append(("one hundred and seventy two thousand", False, 0.0, [(172000.0, 'LONELY_VALUE')], [],))
    cases.append(("one million seventy two thousand", False, 0.0, [(1072000.0, 'LONELY_VALUE')], [],))
    cases.append(("one million and seventy two thousand", False, 0.0, [(1072000.0, 'LONELY_VALUE')], [],))
    cases.append(("one million seventy two thousand five hundred and six", False, 0.0, [(1072506.0, 'LONELY_VALUE')], [],))
    cases.append(("one million seventy two thousand five hundred and six million", False, 0.0, [(1072506000000.0, 'LONELY_VALUE')], [],))

    cases.append(("twenty twenty three seconds", True, 2023.0, [], [(30.0, Scale(scale = 1.0))],))
    cases.append(("twenty 20 three seconds", False, 3.0, [(20.0, "CONSECUTIVE_VALUES"), (20.0, "CONSECUTIVE_VALUES")], [(3.0, Scale(scale = 1.0))],))
    cases.append(("twenty 20 3 seconds", False, 3.0, [(20.0, "CONSECUTIVE_VALUES"), (20.0, "CONSECUTIVE_VALUES")], [(3.0, Scale(scale = 1.0))],))
    cases.append(("twenty 20 3", False, 0.0, [(20.0, "CONSECUTIVE_VALUES"), (20.0, "CONSECUTIVE_VALUES"), (3.0, "LONELY_VALUE"),], [],))
    cases.append(("twenty,18 three seconds", False, 3.0, [(20.0, "CONSECUTIVE_VALUES"), (18.0, "CONSECUTIVE_VALUES")], [(3.0, Scale(scale = 1.0))],))
    cases.append(("twenty 18 three seconds", False, 3.0, [(20.0, "CONSECUTIVE_VALUES"), (18.0, "CONSECUTIVE_VALUES")], [(3.0, Scale(scale = 1.0))],))

    cases.append(("1 minute seconds", False, 60.0, [("seconds", "CONSECUTIVE_SCALES")], [(1.0, Scale(scale = 60.0))],))
    cases.append(("minute 1 seconds", False, 1.0, [("minute", "LEADING_SCALE")], [(1.0, Scale(scale = 1.0))],))
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
    "input, expected_success, expected_seconds, expected_invalid, expected_valid",
    generate_strict_tests(),
)
def test_strict_mode(
    tl_strict,
    input,
    expected_success,
    expected_seconds,
    expected_invalid,
    expected_valid,
):
    tl_strict.content = input
    tl_strict.parse()
    assert tl_strict.result.success is expected_success
    assert tl_strict.result.seconds == expected_seconds
    assert tl_strict.result.invalid == expected_invalid
    for actual_scale, expected_scale in zip(tl_strict.result.valid, expected_valid):
        assert compare_scales(actual_scale[1], expected_scale[1])
