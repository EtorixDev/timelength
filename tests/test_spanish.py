import pytest

from timelength.locales import Spanish
from timelength.timelength import TimeLength
from timelength.dataclasses import Scale


@pytest.fixture
def tl_notstrict():
    return TimeLength(content="0 segundos", strict=False, locale=Spanish())


@pytest.fixture
def tl_strict():
    return TimeLength(content="0 segundos", strict=True, locale=Spanish())


def generate_notstrict_tests():
    cases = []
    # Basic Functionality
    cases.append(("", False, 0.0, [], [],))
    cases.append(("AHHHHH, \u00BFque???###", False, 0.0, [("AHHHHH", "UNKNOWN_TERM"), ("que", "UNKNOWN_TERM"), ("###", "UNKNOWN_TERM"), ("?", "CONSECUTIVE_SPECIALS"), ("?", "CONSECUTIVE_SPECIALS")], [],))
    cases.append(("0", True, 0.0, [], [(0.0, Scale(scale=1.0))],))
    cases.append(("5 segundos", True, 5.0, [], [(5.0, Scale(scale=1.0))],))
    cases.append(("5 segundos 3", True, 5.0, [(3.0, "LONELY_VALUE")], [(5.0, Scale(scale=1.0))],))
    for decimal in Spanish()._decimal_separators:
        cases.append((f"5{decimal}5 segundos", True, 5.5, [], [(5.5, Scale(scale=1.0))],))
    for thousand in Spanish()._thousand_separators:
        cases.append((f"5{thousand}500 segundos", True, 5500.0, [], [(5500.0, Scale(scale=1.0))],))
    for thousand in Spanish()._thousand_separators:
        for decimal in Spanish()._decimal_separators:
            cases.append((f"5{thousand}500{decimal}55 segundos", True, 5500.55, [], [(5500.55, Scale(scale=1.0))],))
    cases.append(("1h5m30s", True, 3930.0, [], [(1.0, Scale(scale=3600.0)), (5.0, Scale(scale=60.0)), (30.0, Scale(scale=1.0))],))
    cases.append(("1 hora 5 minutos 30 segundos", True, 3930.0, [], [(1.0, Scale(scale=3600.0)), (5.0, Scale(scale=60.0)), (30.0, Scale(scale=1.0))],))
    cases.append(("1 hora 5min30s", True, 3930.0, [], [(1.0, Scale(scale=3600.0)), (5.0, Scale(scale=60.0)), (30.0, Scale(scale=1.0))],))

    # Segmentors as of Writing: "," "y" "&"
    cases.append(("1 hora, 5 minutos, y 30 segundos & 7ms", True, 3930.007, [], [(1.0, Scale(scale=3600.0)), (5.0, Scale(scale=60.0)), (30.0, Scale(scale=1.0)), (7.0, Scale(scale=0.001))],))
    cases.append(("5m,, 5s", True, 305.0, [(",", "CONSECUTIVE_SPECIALS")], [(5.0, Scale(scale=60.0)), (5.0, Scale(scale=1.0))],))
    cases.append(("1, 2, 3 minutos", True, 360.0, [], [(6.0, Scale(scale=60.0))],))
    # Connectors as of Writing: " ", "-", "\t"
    cases.append(("1 minuto-2-segundos	3MS", True, 62.003, [], [(1.0, Scale(scale=60.0)), (2.0, Scale(scale=1.0)), (3.0, Scale(scale=0.001))],))

    # Numerals / Modifiers / Multipliers
    cases.append(("cero", True, 0.0, [], [(0.0, Scale(scale=1.0))],))
    cases.append(("cero minutos", True, 0.0, [], [(0.0, Scale(scale=60.0))],))
    cases.append(("cinco", True, 5.0, [], [(5.0, Scale(scale=1.0))],))
    
    cases.append(("veintidós seg", True, 22.0, [], [(22.0, Scale(scale=1.0))],))
    cases.append(("mil segundos", True, 1000.0, [], [(1000.0, Scale(scale=1.0))],))
    cases.append(("un millon segundos", True, 1000000.0, [], [(1000000.0, Scale(scale=1.0))],))
    cases.append(("medio millon segundos", True, 500000.0, [], [(500000.0, Scale(scale=1.0))],))
    cases.append(("un tercio de mil millon de segundos", True, 333333333.3333333, [], [(333333333.3333333, Scale(scale=1.0))],))
    cases.append(("un millon medio de segundos", True, 500000.0, [], [(500000.0, Scale(scale=1.0))],))
    cases.append(("un millon de medio segundos", True, 500000.0, [], [(500000.0, Scale(scale=1.0))],))
    cases.append(("una mitad de minutos", True, 30.0, [], [(0.5, Scale(scale=60.0))],))
    cases.append(("una mitad minutos de ", True, 30.0, [("de", "UNUSED_MULTIPLIER")], [(0.5, Scale(scale=60.0))],))
    cases.append(("la mitad de un millón seg", True, 500000.0, [], [(500000.0, Scale(1.0, "segundo", "segundos"))],))
    
    for item in Spanish()._numerals["multiplier"]["terms"]:
        cases.append((f"dos {item} seis minutos", True, 720.0, [], [(12.0, Scale(scale=60.0))],))
    for item in Spanish()._numerals["multiplier"]["terms"]:
        cases.append((f"2 {item} seis minutos", True, 720.0, [], [(12.0, Scale(scale=60.0))],))
    for item in Spanish()._numerals["multiplier"]["terms"]:
        cases.append((f"dos {item} 6 minutos", True, 720.0, [], [(12.0, Scale(scale=60.0))],))
    for item in Spanish()._numerals["multiplier"]["terms"]:
        cases.append((f"2 {item}", False, 0.0, [(f"{item}", "UNUSED_MULTIPLIER"), (2.0, "LONELY_VALUE")], [],))

    # Numeral Type Combinations + Float/Numeral Combinations
    cases.append(("CINCO horas, 2 minutos, 3s", True, 18123.0, [], [(5.0, Scale(scale=3600.0)), (2.0, Scale(scale=60.0)), (3.0, Scale(scale=1.0))],))
    cases.append(("1 2 segundos", True, 2.0, [(1.0, "CONSECUTIVE_VALUES")], [(2.0, Scale(scale=1.0))],))
    cases.append(("un dos segundos", True, 12.0, [], [(12.0, Scale(scale=1.0))],))
    cases.append(("1 dos segundos", True, 2.0, [(1.0, "CONSECUTIVE_VALUES")], [(2.0, Scale(scale=1.0))],))
    cases.append(("un 2 segundos", True, 2.0, [(1.0, "CONSECUTIVE_VALUES")], [(2.0, Scale(scale=1.0))],))

    cases.append(("1 13 segundos", True, 13.0, [(1.0, "CONSECUTIVE_VALUES")], [(13.0, Scale(scale=1.0))],))
    cases.append(("un trece segundos", True, 113.0, [], [(113.0, Scale(scale=1.0))],))
    cases.append(("1 trece segundos", True, 13.0, [(1.0, "CONSECUTIVE_VALUES")], [(13.0, Scale(scale=1.0))],))
    cases.append(("un 13 segundos", True, 13.0, [(1.0, "CONSECUTIVE_VALUES")], [(13.0, Scale(scale=1.0))],))

    cases.append(("1 50 segundos", True, 50.0, [(1.0, "CONSECUTIVE_VALUES")], [(50.0, Scale(scale=1.0))],))
    cases.append(("un cincuenta segundos", True, 150.0, [], [(150.0, Scale(scale=1.0))],))
    cases.append(("1 cincuenta segundos", True, 50.0, [(1.0, "CONSECUTIVE_VALUES")], [(50.0, Scale(scale=1.0))],))
    cases.append(("un 50 segundos", True, 50.0, [(1.0, "CONSECUTIVE_VALUES")], [(50.0, Scale(scale=1.0))],))

    cases.append(("3 100 segundos", True, 3100.0, [], [(3100.0, Scale(scale=1.0))],))
    cases.append(("tres cien segundos", True, 300.0, [], [(300.0, Scale(scale=1.0))],))
    cases.append(("3 cien segundos", True, 300.0, [], [(300.0, Scale(scale=1.0))],))
    cases.append(("tres 100 segundos", True, 100.0, [(3.0, "CONSECUTIVE_VALUES")], [(100.0, Scale(scale=1.0))],))
    cases.append(("tres un cien segundos", True, 3100.0, [], [(3100.0, Scale(scale=1.0))],))
    cases.append(("tres 1 cien segundos", True, 100.0, [(3.0, "CONSECUTIVE_VALUES")], [(100.0, Scale(scale=1.0))],))
    cases.append(("3 un cien segundos", True, 100.0, [(3.0, "CONSECUTIVE_VALUES")], [(100.0, Scale(scale=1.0))],))

    cases.append(("15 5 segundos", True, 5.0, [(15.0, "CONSECUTIVE_VALUES")], [(5.0, Scale(scale=1.0))],))
    cases.append(("quince cinco segundos", True, 5.0, [(15.0, "CONSECUTIVE_VALUES")], [(5.0, Scale(scale=1.0))],))
    cases.append(("15 cinco segundos", True, 5.0, [(15.0, "CONSECUTIVE_VALUES")], [(5.0, Scale(scale=1.0))],))
    cases.append(("quince 5 segundos", True, 5.0, [(15.0, "CONSECUTIVE_VALUES")], [(5.0, Scale(scale=1.0))],))

    cases.append(("15 15 segundos", True, 15.0, [(15.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale=1.0))],))
    cases.append(("quince quince segundos", True, 1515.0, [], [(1515.0, Scale(scale=1.0))],))
    cases.append(("15 quince segundos", True, 15.0, [(15.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale=1.0))],))
    cases.append(("quince 15 segundos", True, 15.0, [(15.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale=1.0))],))

    cases.append(("15 20 segundos", True, 20.0, [(15.0, "CONSECUTIVE_VALUES")], [(20.0, Scale(scale=1.0))],))
    cases.append(("quince veinte segundos", True, 1520.0, [], [(1520.0, Scale(scale=1.0))],))
    cases.append(("15 veinte segundos", True, 20.0, [(15.0, "CONSECUTIVE_VALUES")], [(20.0, Scale(scale=1.0))],))
    cases.append(("quince 20 segundos", True, 20.0, [(15.0, "CONSECUTIVE_VALUES")], [(20.0, Scale(scale=1.0))],))

    cases.append(("20 1 segundos", True, 1.0, [(20.0, "CONSECUTIVE_VALUES")], [(1.0, Scale(scale=1.0))],))
    cases.append(("veinte un segundos", True, 21.0, [], [(21.0, Scale(scale=1.0))],))
    cases.append(("20 un segundos", True, 1.0, [(20.0, "CONSECUTIVE_VALUES")], [(1.0, Scale(scale=1.0))],))
    cases.append(("veinte 1 segundos", True, 1.0, [(20.0, "CONSECUTIVE_VALUES")], [(1.0, Scale(scale=1.0))],))

    cases.append(("20 15 segundos", True, 15.0, [(20.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale=1.0))],))
    cases.append(("veinte quince segundos", True, 2015.0, [], [(2015.0, Scale(scale=1.0))],))
    cases.append(("20 quince segundos", True, 15.0, [(20.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale=1.0))],))
    cases.append(("veinte 15 segundos", True, 15.0, [(20.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale=1.0))],))

    cases.append(("20 30 segundos", True, 30.0, [(20.0, "CONSECUTIVE_VALUES")], [(30.0, Scale(scale=1.0))],))
    cases.append(("veinte treinta segundos", True, 2030.0, [], [(2030.0, Scale(scale=1.0))],))
    cases.append(("20 treinta segundos", True, 30.0, [(20.0, "CONSECUTIVE_VALUES")], [(30.0, Scale(scale=1.0))],))
    cases.append(("veinte 30 segundos", True, 30.0, [(20.0, "CONSECUTIVE_VALUES")], [(30.0, Scale(scale=1.0))],))

    cases.append(("1 minuto segundos", True, 60.0, [("segundos", "CONSECUTIVE_SCALES")], [(1.0, Scale(scale=60.0))],))
    cases.append(("minuto 1 segundos", True, 1.0, [("minuto", "LEADING_SCALE")], [(1.0, Scale(scale=1.0))],))
    return cases


def generate_strict_tests():
    cases = []
    # Basic Functionality
    cases.append(("", False, 0.0, [], [],))
    cases.append(("AHHHHH, \u00BFque???###", False, 0.0, [("AHHHHH", "UNKNOWN_TERM"), ("que", "UNKNOWN_TERM"), ("###", "UNKNOWN_TERM"), ("?", "CONSECUTIVE_SPECIALS"), ("?", "CONSECUTIVE_SPECIALS")], [],))
    cases.append(("0", False, 0.0, [(0.0, "LONELY_VALUE")], [],))
    cases.append(("5 segundos", True, 5.0, [], [(5.0, Scale(scale=1.0))],))
    cases.append(("5 segundos 3", False, 5.0, [(3.0, "LONELY_VALUE")], [(5.0, Scale(scale=1.0))],))
    for decimal in Spanish()._decimal_separators:
        cases.append((f"5{decimal}5 segundos", True, 5.5, [], [(5.5, Scale(scale=1.0))],))
    for thousand in Spanish()._thousand_separators:
        cases.append((f"5{thousand}500 segundos", True, 5500.0, [], [(5500.0, Scale(scale=1.0))],))
    for thousand in Spanish()._thousand_separators:
        for decimal in Spanish()._decimal_separators:
            cases.append((f"5{thousand}500{decimal}55 segundos", True, 5500.55, [], [(5500.55, Scale(scale=1.0))],))
    cases.append(("1h5m30s", True, 3930.0, [], [(1.0, Scale(scale=3600.0)), (5.0, Scale(scale=60.0)), (30.0, Scale(scale=1.0))],))
    cases.append(("1 hora 5 minutos 30 segundos", True, 3930.0, [], [(1.0, Scale(scale=3600.0)), (5.0, Scale(scale=60.0)), (30.0, Scale(scale=1.0))],))
    cases.append(("1 hora 5min30s", True, 3930.0, [], [(1.0, Scale(scale=3600.0)), (5.0, Scale(scale=60.0)), (30.0, Scale(scale=1.0))],))

    # Segmentors as of Writing: "," "y" "&"
    cases.append(("1 hora, 5 minutos, y 30 segundos & 7ms", True, 3930.007, [], [(1.0, Scale(scale=3600.0)), (5.0, Scale(scale=60.0)), (30.0, Scale(scale=1.0)), (7.0, Scale(scale=0.001))],))
    cases.append(("5m,, 5s", False, 305.0, [(",", "CONSECUTIVE_SPECIALS")], [(5.0, Scale(scale=60.0)), (5.0, Scale(scale=1.0))],))
    cases.append(("1, 2, 3 minutos", True, 360.0, [], [(6.0, Scale(scale=60.0))],))
    # Connectors as of Writing: " ", "-", "\t"
    cases.append(("1 minuto-2-segundos	3MS", True, 62.003, [], [(1.0, Scale(scale=60.0)), (2.0, Scale(scale=1.0)), (3.0, Scale(scale=0.001))],))

    # Numerals / Modifiers / Multipliers
    cases.append(("cero", False, 0.0, [(0.0, "LONELY_VALUE")], [],))
    cases.append(("cero minutos", True, 0.0, [], [(0.0, Scale(scale=60.0))],))
    cases.append(("cinco", False, 0.0, [(5.0, "LONELY_VALUE")], [],))

    cases.append(("veintidós seg", True, 22.0, [], [(22.0, Scale(scale=1.0))],))
    cases.append(("mil segundos", True, 1000.0, [], [(1000.0, Scale(scale=1.0))],))
    cases.append(("un millon segundos", True, 1000000.0, [], [(1000000.0, Scale(scale=1.0))],))
    cases.append(("medio millon segundos", True, 500000.0, [], [(500000.0, Scale(scale=1.0))],))
    cases.append(("un tercio de mil millon de segundos", True, 333333333.3333333, [], [(333333333.3333333, Scale(scale=1.0))],))
    cases.append(("un millon medio de segundos", True, 500000.0, [], [(500000.0, Scale(scale=1.0))],))
    cases.append(("un millon de medio segundos", True, 500000.0, [], [(500000.0, Scale(scale=1.0))],))
    cases.append(("una mitad de minutos", True, 30.0, [], [(0.5, Scale(scale=60.0))],))
    cases.append(("una mitad minutos de ", False, 30.0, [("de", "UNUSED_MULTIPLIER")], [(0.5, Scale(scale=60.0))],))
    cases.append(("la mitad de un millón seg", True, 500000.0, [], [(500000.0, Scale(1.0, "segundo", "segundos"))],))

    for item in Spanish()._numerals["multiplier"]["terms"]:
        cases.append((f"dos {item} seis minutos", True, 720.0, [], [(12.0, Scale(scale=60.0))],))
    for item in Spanish()._numerals["multiplier"]["terms"]:
        cases.append((f"2 {item} seis minutos", True, 720.0, [], [(12.0, Scale(scale=60.0))],))
    for item in Spanish()._numerals["multiplier"]["terms"]:
        cases.append((f"dos {item} 6 minutos", True, 720.0, [], [(12.0, Scale(scale=60.0))],))
    for item in Spanish()._numerals["multiplier"]["terms"]:
        cases.append((f"2 {item}", False, 0.0, [(f"{item}", "UNUSED_MULTIPLIER"), (2.0, "LONELY_VALUE")], [],))

    # Numeral Type Combinations + Float/Numeral Combinations
    cases.append(("CINCO horas, 2 minutos, 3s", True, 18123.0, [], [(5.0, Scale(scale=3600.0)), (2.0, Scale(scale=60.0)), (3.0, Scale(scale=1.0))],))
    cases.append(("1 2 segundos", False, 2.0, [(1.0, "CONSECUTIVE_VALUES")], [(2.0, Scale(scale=1.0))],))
    cases.append(("un dos segundos", True, 12.0, [], [(12.0, Scale(scale=1.0))],))
    cases.append(("1 dos segundos", False, 2.0, [(1.0, "CONSECUTIVE_VALUES")], [(2.0, Scale(scale=1.0))],))
    cases.append(("un 2 segundos", False, 2.0, [(1.0, "CONSECUTIVE_VALUES")], [(2.0, Scale(scale=1.0))],))

    cases.append(("1 13 segundos", False, 13.0, [(1.0, "CONSECUTIVE_VALUES")], [(13.0, Scale(scale=1.0))],))
    cases.append(("un trece segundos", True, 113.0, [], [(113.0, Scale(scale=1.0))],))
    cases.append(("1 trece segundos", False, 13.0, [(1.0, "CONSECUTIVE_VALUES")], [(13.0, Scale(scale=1.0))],))
    cases.append(("un 13 segundos", False, 13.0, [(1.0, "CONSECUTIVE_VALUES")], [(13.0, Scale(scale=1.0))],))

    cases.append(("1 50 segundos", False, 50.0, [(1.0, "CONSECUTIVE_VALUES")], [(50.0, Scale(scale=1.0))],))
    cases.append(("un cincuenta segundos", True, 150.0, [], [(150.0, Scale(scale=1.0))],))
    cases.append(("1 cincuenta segundos", False, 50.0, [(1.0, "CONSECUTIVE_VALUES")], [(50.0, Scale(scale=1.0))],))
    cases.append(("un 50 segundos", False, 50.0, [(1.0, "CONSECUTIVE_VALUES")], [(50.0, Scale(scale=1.0))],))

    cases.append(("3 100 segundos", True, 3100.0, [], [(3100.0, Scale(scale=1.0))],))
    cases.append(("tres cien segundos", True, 300.0, [], [(300.0, Scale(scale=1.0))],))
    cases.append(("3 cien segundos", True, 300.0, [], [(300.0, Scale(scale=1.0))],))
    cases.append(("tres 100 segundos", False, 100.0, [(3.0, "CONSECUTIVE_VALUES")], [(100.0, Scale(scale=1.0))],))
    cases.append(("tres un cien segundos", True, 3100.0, [], [(3100.0, Scale(scale=1.0))],))
    cases.append(("tres 1 cien segundos", False, 100.0, [(3.0, "CONSECUTIVE_VALUES")], [(100.0, Scale(scale=1.0))],))
    cases.append(("3 un cien segundos", False, 100.0, [(3.0, "CONSECUTIVE_VALUES")], [(100.0, Scale(scale=1.0))],))

    cases.append(("15 5 segundos", False, 5.0, [(15.0, "CONSECUTIVE_VALUES")], [(5.0, Scale(scale=1.0))],))
    cases.append(("quince cinco segundos", False, 5.0, [(15.0, "CONSECUTIVE_VALUES")], [(5.0, Scale(scale=1.0))],))
    cases.append(("15 cinco segundos", False, 5.0, [(15.0, "CONSECUTIVE_VALUES")], [(5.0, Scale(scale=1.0))],))
    cases.append(("quince 5 segundos", False, 5.0, [(15.0, "CONSECUTIVE_VALUES")], [(5.0, Scale(scale=1.0))],))

    cases.append(("15 15 segundos", False, 15.0, [(15.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale=1.0))],))
    cases.append(("quince quince segundos", True, 1515.0, [], [(1515.0, Scale(scale=1.0))],))
    cases.append(("15 quince segundos", False, 15.0, [(15.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale=1.0))],))
    cases.append(("quince 15 segundos", False, 15.0, [(15.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale=1.0))],))

    cases.append(("15 20 segundos", False, 20.0, [(15.0, "CONSECUTIVE_VALUES")], [(20.0, Scale(scale=1.0))],))
    cases.append(("quince veinte segundos", True, 1520.0, [], [(1520.0, Scale(scale=1.0))],))
    cases.append(("15 veinte segundos", False, 20.0, [(15.0, "CONSECUTIVE_VALUES")], [(20.0, Scale(scale=1.0))],))
    cases.append(("quince 20 segundos", False, 20.0, [(15.0, "CONSECUTIVE_VALUES")], [(20.0, Scale(scale=1.0))],))

    cases.append(("20 1 segundos", False, 1.0, [(20.0, "CONSECUTIVE_VALUES")], [(1.0, Scale(scale=1.0))],))
    cases.append(("veinte un segundos", True, 21.0, [], [(21.0, Scale(scale=1.0))],))
    cases.append(("20 un segundos", False, 1.0, [(20.0, "CONSECUTIVE_VALUES")], [(1.0, Scale(scale=1.0))],))
    cases.append(("veinte 1 segundos", False, 1.0, [(20.0, "CONSECUTIVE_VALUES")], [(1.0, Scale(scale=1.0))],))

    cases.append(("20 15 segundos", False, 15.0, [(20.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale=1.0))],))
    cases.append(("veinte quince segundos", True, 2015.0, [], [(2015.0, Scale(scale=1.0))],))
    cases.append(("20 quince segundos", False, 15.0, [(20.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale=1.0))],))
    cases.append(("veinte 15 segundos", False, 15.0, [(20.0, "CONSECUTIVE_VALUES")], [(15.0, Scale(scale=1.0))],))

    cases.append(("20 30 segundos", False, 30.0, [(20.0, "CONSECUTIVE_VALUES")], [(30.0, Scale(scale=1.0))],))
    cases.append(("veinte treinta segundos", True, 2030.0, [], [(2030.0, Scale(scale=1.0))],))
    cases.append(("20 treinta segundos", False, 30.0, [(20.0, "CONSECUTIVE_VALUES")], [(30.0, Scale(scale=1.0))],))
    cases.append(("veinte 30 segundos", False, 30.0, [(20.0, "CONSECUTIVE_VALUES")], [(30.0, Scale(scale=1.0))],))

    cases.append(("1 minuto segundos", False, 60.0, [("segundos", "CONSECUTIVE_SCALES")], [(1.0, Scale(scale=60.0))],))
    cases.append(("minuto 1 segundos", False, 1.0, [("minuto", "LEADING_SCALE")], [(1.0, Scale(scale=1.0))],))
    return cases


def compare_scales(scale1, scale2):
    """Compare dos Scale objects based on the `scale` attribute."""
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
