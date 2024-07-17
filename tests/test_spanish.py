import pytest

from timelength.enums import FailureFlags
from timelength.locales import Spanish
from timelength.timelength import TimeLength
from timelength.dataclasses import Scale, ParserSettings


@pytest.fixture
def tl_notstrict():
    return TimeLength(
        content = "0 segundos", 
        locale = Spanish()
    )


@pytest.fixture
def tl_strict():
    return TimeLength(
        content = "0 segundos", 
        locale = Spanish(
            flags = FailureFlags.ALL, 
            settings = ParserSettings(allow_duplicate_scales = False)
        )
    )
    

def generate_notstrict_tests():
    cases = []
    # Basic Functionality
    cases.append(("", False, 0.0, [], [],))
    cases.append(("AHHHHH, \u00BFque???###", False, 0.0, [("AHHHHH", FailureFlags.UNKNOWN_TERM), ("que", FailureFlags.UNKNOWN_TERM), ("?", FailureFlags.CONSECUTIVE_SPECIAL), ("?", FailureFlags.CONSECUTIVE_SPECIAL), ("###", FailureFlags.UNKNOWN_TERM)], [],))
    cases.append(("0", True, 0.0, [], [(0.0, Scale(scale = 1.0))],))
    cases.append(("5 segundos", True, 5.0, [], [(5.0, Scale(scale = 1.0))],))
    cases.append(("5 segundos 3", True, 5.0, [(3.0, FailureFlags.LONELY_VALUE)], [(5.0, Scale(scale = 1.0))],))
    for decimal in Spanish()._decimal_delimiters:
        cases.append((f"5{decimal}5 segundos", True, 5.5, [], [(5.5, Scale(scale = 1.0))],))
    for thousand in Spanish()._thousand_delimiters:
        cases.append((f"5{thousand}500 segundos", True, 5500.0, [], [(5500.0, Scale(scale = 1.0))],))
    for thousand in Spanish()._thousand_delimiters:
        for decimal in Spanish()._decimal_delimiters:
            cases.append((f"5{thousand}500{decimal}55 segundos", True, 5500.55, [], [(5500.55, Scale(scale = 1.0))],))
    cases.append(("1h5m30s", True, 3930.0, [], [(1.0, Scale(scale = 3600.0)), (5.0, Scale(scale = 60.0)), (30.0, Scale(scale = 1.0))],))
    cases.append(("1 hora 5 minutos 30 segundos", True, 3930.0, [], [(1.0, Scale(scale = 3600.0)), (5.0, Scale(scale = 60.0)), (30.0, Scale(scale = 1.0))],))
    cases.append(("1 hora 5min30s", True, 3930.0, [], [(1.0, Scale(scale = 3600.0)), (5.0, Scale(scale = 60.0)), (30.0, Scale(scale = 1.0))],))

    # Segmentors as of Writing: "," "y" "&"
    cases.append(("1 hora, 5 minutos, y 30 segundos & 7ms", True, 3930.007, [], [(1.0, Scale(scale = 3600.0)), (5.0, Scale(scale = 60.0)), (30.0, Scale(scale = 1.0)), (7.0, Scale(scale = 0.001))],))
    cases.append(("5m,, 5s", True, 305.0, [(",", FailureFlags.CONSECUTIVE_SEGMENTOR)], [(5.0, Scale(scale = 60.0)), (5.0, Scale(scale = 1.0))],))
    cases.append(("1, 2, 3 minutos", True, 360.0, [], [(6.0, Scale(scale = 60.0))],))
    # Connectors as of Writing: " ", "-", "\t"
    cases.append(("1 minuto-2-segundos	3MS", True, 62.003, [], [(1.0, Scale(scale = 60.0)), (2.0, Scale(scale = 1.0)), (3.0, Scale(scale = 0.001))],))
    cases.append(("5m,   5s", True, 305.0, [(" ", FailureFlags.CONSECUTIVE_CONNECTOR)], [(5.0, Scale(scale = 60.0)), (5.0, Scale(scale = 1.0))],))

    # Numerals / Modifiers / Multipliers
    cases.append(("cero", True, 0.0, [], [(0.0, Scale(scale = 1.0))],))
    cases.append(("cero minutos", True, 0.0, [], [(0.0, Scale(scale = 60.0))],))
    cases.append(("cinco", True, 5.0, [], [(5.0, Scale(scale = 1.0))],))
    
    cases.append(("un mil", True, 1000.0, [], [],))
    cases.append(("un mil y cinco", True, 1005.0, [], [],))
    cases.append(("un mil segundos y cinco", True, 1000.0, [(5.0, FailureFlags.LONELY_VALUE)], [],))

    cases.append(("medio", True, 0.5, [], [(0.5, Scale(scale = 1.0))],))
    cases.append(("medio min", True, 30.0, [], [(0.5, Scale(scale = 60.0))],))
    cases.append(("veintitrés de medio min", True, 690, [], [(11.5, Scale(scale = 60))],))
    cases.append(("veintitrés medio de min", True, 690, [], [(11.5, Scale(scale = 60))],))
    cases.append(("medio de veintitrés min", True, 690, [], [(11.5, Scale(scale = 60))],))
    cases.append(("medio veintitrés min", True, 690, [], [(11.5, Scale(scale = 60))],))
    cases.append(("medio medio veintitrés min", True, 345, [], [(5.75, Scale(scale = 60))],))
    cases.append(("medio de medio de veintitrés min", True, 345, [], [(5.75, Scale(scale = 60))],))
    cases.append(("medio de medio veintitrés min", True, 345, [], [(5.75, Scale(scale = 60))],))
    cases.append(("medio medio de veintitrés min", True, 345, [], [(5.75, Scale(scale = 60))],))
    cases.append(("veintitrés de medio medio mins", True, 345, [], [(5.75, Scale(scale = 60))],))
    cases.append(("veintitrés medio medio de min", True, 345, [], [(5.75, Scale(scale = 60))],))
    cases.append(("un millón de segundos medio", True, 1000000.0, [(0.5, FailureFlags.LONELY_VALUE)], [(1000000.0, Scale(scale = 1.0))],))
    cases.append(("un millón de segundos medio de", True, 1000000.0, [("de", FailureFlags.UNUSED_MULTIPLIER), (0.5, FailureFlags.LONELY_VALUE)], [(1000000.0, Scale(scale = 1.0))],))
    
    cases.append(("veintidos seg", True, 22.0, [], [(22.0, Scale(scale = 1.0))],))
    cases.append(("mil segundos", True, 1000.0, [], [(1000.0, Scale(scale = 1.0))],))
    cases.append(("un millon segundos", True, 1000000.0, [], [(1000000.0, Scale(scale = 1.0))],))
    cases.append(("medio de millon segundos", True, 500000.0, [], [(500000.0, Scale(scale = 1.0))],))
    cases.append(("medio millon segundos", True, 500000.0, [], [(500000.0, Scale(scale = 1.0))],))
    cases.append(("un tercio de mil millon de segundos", True, 333333333.3333333, [], [(333333333.3333333, Scale(scale = 1.0))],))
    cases.append(("un millon medio de segundos", True, 500000.0, [], [(500000.0, Scale(scale = 1.0))],))
    cases.append(("un millon de medio segundos", True, 500000.0, [], [(500000.0, Scale(scale = 1.0))],))
    cases.append(("una mitad de minutos", True, 30.0, [], [(0.5, Scale(scale = 60.0))],))
    cases.append(("una mitad minutos de ", True, 30.0, [("de", FailureFlags.UNUSED_MULTIPLIER)], [(0.5, Scale(scale = 60.0))],))
    cases.append(("la mitad de un millon seg", True, 500000.0, [], [(500000.0, Scale(scale = 1.0))],))
    cases.append(("dos mil quinientos minutos y medio de un millón doscientos cincuenta y seis mil segundos", True, 778000.0, [], [(2500.0, Scale(scale = 60.0)), (628000.0, Scale(scale = 1.0))],))
    
    cases.append((f"dos de seis minutos", True, 720.0, [], [(12.0, Scale(scale = 60.0))],))
    cases.append((f"2 de seis minutos", True, 720.0, [], [(12.0, Scale(scale = 60.0))],))
    cases.append((f"dos de 6 minutos", True, 720.0, [], [(12.0, Scale(scale = 60.0))],))
    cases.append((f"2 de", False, 0.0, [(f"de", FailureFlags.UNUSED_MULTIPLIER), (2.0, FailureFlags.LONELY_VALUE)], [],))

    # Numeral Type Combinations + Float/Numeral Combinations
    cases.append(("CINCO horas, 2 minutos, 3s", True, 18123.0, [], [(5.0, Scale(scale = 3600.0)), (2.0, Scale(scale = 60.0)), (3.0, Scale(scale = 1.0))],))
    cases.append(("1 2 segundos", True, 2.0, [(1.0, FailureFlags.CONSECUTIVE_VALUE)], [(2.0, Scale(scale = 1.0))],))
    cases.append(("un dos segundos", True, 12.0, [], [(12.0, Scale(scale = 1.0))],))
    cases.append(("1 dos segundos", True, 2.0, [(1.0, FailureFlags.CONSECUTIVE_VALUE)], [(2.0, Scale(scale = 1.0))],))
    cases.append(("un 2 segundos", True, 2.0, [(1.0, FailureFlags.CONSECUTIVE_VALUE)], [(2.0, Scale(scale = 1.0))],))

    cases.append(("1 13 segundos", True, 13.0, [(1.0, FailureFlags.CONSECUTIVE_VALUE)], [(13.0, Scale(scale = 1.0))],))
    cases.append(("un trece segundos", True, 113.0, [], [(113.0, Scale(scale = 1.0))],))
    cases.append(("1 trece segundos", True, 13.0, [(1.0, FailureFlags.CONSECUTIVE_VALUE)], [(13.0, Scale(scale = 1.0))],))
    cases.append(("un 13 segundos", True, 13.0, [(1.0, FailureFlags.CONSECUTIVE_VALUE)], [(13.0, Scale(scale = 1.0))],))

    cases.append(("1 50 segundos", True, 50.0, [(1.0, FailureFlags.CONSECUTIVE_VALUE)], [(50.0, Scale(scale = 1.0))],))
    cases.append(("un cincuenta segundos", True, 150.0, [], [(150.0, Scale(scale = 1.0))],))
    cases.append(("1 cincuenta segundos", True, 50.0, [(1.0, FailureFlags.CONSECUTIVE_VALUE)], [(50.0, Scale(scale = 1.0))],))
    cases.append(("un 50 segundos", True, 50.0, [(1.0, FailureFlags.CONSECUTIVE_VALUE)], [(50.0, Scale(scale = 1.0))],))

    cases.append(("3 100 segundos", True, 3100.0, [], [(3100.0, Scale(scale = 1.0))],))
    cases.append(("tres cien segundos", True, 300.0, [], [(300.0, Scale(scale = 1.0))],))
    cases.append(("3 cien segundos", True, 300.0, [], [(300.0, Scale(scale = 1.0))],))
    cases.append(("tres 100 segundos", True, 100.0, [(3.0, FailureFlags.CONSECUTIVE_VALUE)], [(100.0, Scale(scale = 1.0))],))
    cases.append(("tres un cien segundos", True, 3100.0, [], [(3100.0, Scale(scale = 1.0))],))
    cases.append(("tres 1 cien segundos", True, 100.0, [(3.0, FailureFlags.CONSECUTIVE_VALUE)], [(100.0, Scale(scale = 1.0))],))
    cases.append(("3 un cien segundos", True, 100.0, [(3.0, FailureFlags.CONSECUTIVE_VALUE)], [(100.0, Scale(scale = 1.0))],))

    cases.append(("15 5 segundos", True, 5.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(5.0, Scale(scale = 1.0))],))
    cases.append(("quince cinco segundos", True, 5.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(5.0, Scale(scale = 1.0))],))
    cases.append(("15 cinco segundos", True, 5.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(5.0, Scale(scale = 1.0))],))
    cases.append(("quince 5 segundos", True, 5.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(5.0, Scale(scale = 1.0))],))

    cases.append(("15 15 segundos", True, 15.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(15.0, Scale(scale = 1.0))],))
    cases.append(("quince quince segundos", True, 1515.0, [], [(1515.0, Scale(scale = 1.0))],))
    cases.append(("15 quince segundos", True, 15.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(15.0, Scale(scale = 1.0))],))
    cases.append(("quince 15 segundos", True, 15.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(15.0, Scale(scale = 1.0))],))

    cases.append(("15 20 segundos", True, 20.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(20.0, Scale(scale = 1.0))],))
    cases.append(("quince veinte segundos", True, 1520.0, [], [(1520.0, Scale(scale = 1.0))],))
    cases.append(("15 veinte segundos", True, 20.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(20.0, Scale(scale = 1.0))],))
    cases.append(("quince 20 segundos", True, 20.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(20.0, Scale(scale = 1.0))],))

    cases.append(("20 1 segundos", True, 1.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE)], [(1.0, Scale(scale = 1.0))],))
    cases.append(("veinte un segundos", True, 21.0, [], [(21.0, Scale(scale = 1.0))],))
    cases.append(("20 un segundos", True, 1.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE)], [(1.0, Scale(scale = 1.0))],))
    cases.append(("veinte 1 segundos", True, 1.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE)], [(1.0, Scale(scale = 1.0))],))

    cases.append(("20 15 segundos", True, 15.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE)], [(15.0, Scale(scale = 1.0))],))
    cases.append(("veinte quince segundos", True, 2015.0, [], [(2015.0, Scale(scale = 1.0))],))
    cases.append(("20 quince segundos", True, 15.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE)], [(15.0, Scale(scale = 1.0))],))
    cases.append(("veinte 15 segundos", True, 15.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE)], [(15.0, Scale(scale = 1.0))],))

    cases.append(("20 30 segundos", True, 30.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE)], [(30.0, Scale(scale = 1.0))],))
    cases.append(("veinte treinta segundos", True, 2030.0, [], [(2030.0, Scale(scale = 1.0))],))
    cases.append(("20 treinta segundos", True, 30.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE)], [(30.0, Scale(scale = 1.0))],))
    cases.append(("veinte 30 segundos", True, 30.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE)], [(30.0, Scale(scale = 1.0))],))
    cases.append(("veinte veinte tres segundos", True, 2023.0, [], [(2023.0, Scale(scale = 1.0))],))
    cases.append(("veinte 20 tres segundos", True, 3.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE), (20.0, FailureFlags.CONSECUTIVE_VALUE)], [(3.0, Scale(scale = 1.0))],))
    cases.append(("veinte 20 3 segundos", True, 3.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE), (20.0, FailureFlags.CONSECUTIVE_VALUE)], [(3.0, Scale(scale = 1.0))],))
    cases.append(("veinte 20 3", False, 0.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE), (20.0, FailureFlags.CONSECUTIVE_VALUE), (3.0, FailureFlags.LONELY_VALUE)], [],))
    cases.append(("1 minuto segundos", True, 60.0, [("segundos", FailureFlags.CONSECUTIVE_SCALE)], [(1.0, Scale(scale = 60.0))],))
    cases.append(("minuto 1 segundos", True, 1.0, [("minuto", FailureFlags.LEADING_SCALE)], [(1.0, Scale(scale = 1.0))],))

    # Long Numerals + Segmentor Combinations
    cases.append(("veintitrés mil seg", True, 23000.0, [], [(23000.0, Scale(scale = 1.0))],))
    cases.append(("dos mil veintitrés seg", True, 2023.0, [], [(30.0, Scale(scale = 1.0))],))
    cases.append(("dos mil veintitrés cinco seg", True, 5.0, [(2023.0, FailureFlags.CONSECUTIVE_VALUE)], [(5.0, Scale(scale = 1.0))],))
    cases.append(("dos mil veintitrés mil cinco seg", True, 23005.0, [(2000.0, FailureFlags.LONELY_VALUE)], [(23005.0, Scale(scale = 1.0))],))
    cases.append(("dos mil veintitrés cinco segundos", True, 5.0, [(2023.0, FailureFlags.CONSECUTIVE_VALUE)], [(5.0, Scale(scale = 1.0))],))
    cases.append(("un mil cinco y cien", True, 1500.0, [], [(1500.0, Scale(scale = 1.0))],))
    cases.append(("un mil 5 y cien", True, 1500.0, [], [(1500.0, Scale(scale = 1.0))],))

    cases.append(("ciento setenta dos mil", True, 172000.0, [], [(172000.0, Scale(scale = 1.0))],))
    cases.append(("ciento setenta y dos mil", True, 172000.0, [], [(172000.0, Scale(scale = 1.0))],))
    cases.append(("un millón setenta dos mil", True, 1072000.0, [], [(1072000.0, Scale(scale = 1.0))],))
    cases.append(("un millón y setenta dos mil", True, 1072000.0, [], [(1072000.0, Scale(scale = 1.0))],))
    cases.append(("un millón setenta dos mil quinientos y seis", True, 1072506.0, [], [(1072506.0, Scale(scale = 1.0))],))
    cases.append(("un millón setenta y dos mil quinientos seis", True, 1072506.0, [], [(1072506.0, Scale(scale = 1.0))],))
    cases.append(("un millón setenta dos mil quinientos y seis millones", True, 1072506000000.0, [], [(1072506000000.0, Scale(scale = 1.0))],))

    # Awkward Thousands/Decimals
    cases.append(("veinte,18 tres segundos", True, 3.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE), (18.0, FailureFlags.CONSECUTIVE_VALUE)], [(3.0, Scale(scale = 1.0))],))
    cases.append(("veinte ,18 tres segundos", True, 3.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE), (0.18, FailureFlags.CONSECUTIVE_VALUE)], [(3.0, Scale(scale = 1.0))],))
    cases.append(("veinte 18 tres segundos", True, 3.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE), (18.0, FailureFlags.CONSECUTIVE_VALUE)], [(3.0, Scale(scale = 1.0))],))
    
    # HHMMSS + Combinations
    cases.append(("12:30:15,25", True, 45015.25, [], [(12.0, Scale(scale = 3600.0)), (30.0, Scale(scale = 60.0)), (15.25, Scale(scale = 1.0))],))
    cases.append(("22: 5", True, 1325.0, [], [(22.0, Scale(scale = 60.0)), (5.0, Scale(scale = 1.0))],))
    cases.append(("1:2:22:33 558:66:77,1234", True, 126558437.1234, [], [(1.0, Scale(scale = 2635200.0)), (2.0, Scale(scale = 604800.0)), (22.0, Scale(scale = 86400.0)), (33558.0, Scale(scale = 3600.0)), (66.0, Scale(scale = 60.0)), (77.1234, Scale(scale = 1.0))],))
    cases.append(("1 dia 2:30:15,25", True, 95415.25, [], [(1.0, Scale(scale = 86400.0)), (2.0, Scale(scale = 3600.0)), (30.0, Scale(scale = 60.0)), (15.25, Scale(scale = 1.0))],))
    cases.append(("22: 2.455: 5555", True, 232055.0, [], [(22.0, Scale(scale = 3600.0)), (2455.0, Scale(scale = 60.0)), (5555.0, Scale(scale = 1.0))],))
    cases.append(("22:  +2.455: 5555", False, 0.0, [("22:  +2.455: 5555", FailureFlags.MALFORMED_HHMMSS)], [],))
    cases.append(("22: 2.455 : 5555", False, 0.0, [("22: 2.455 : 5555", FailureFlags.MALFORMED_HHMMSS)], [],))
    cases.append(("22: 2.455 5: 5555", True, 9630.0, [], [(22.0, Scale(scale = 60.0)), (2455.0, Scale(scale = 1.0)), (5.0, Scale(scale = 60.0)), (5555.0, Scale(scale = 1.0))],))
    cases.append(("22: 2 455: +5555", True, 232055.0, [], [(22.0, Scale(scale = 3600.0)), (2455.0, Scale(scale = 60.0)), (5555.0, Scale(scale = 1.0))],))
    cases.append(("22: 2.455: ++5555", False, 0.0, [("22: 2.455: ++5555", FailureFlags.MALFORMED_HHMMSS)], [],))
    cases.append(("2:55 5 minutos", True, 475.0, [], [(2.0, Scale(scale = 60.0)), (55.0, Scale(scale = 1.0)), (5.0, Scale(scale = 60.0))],))
    cases.append(("2: 6 5: 2", True, 428.0, [], [(2.0, Scale(scale = 60.0)), (6.0, Scale(scale = 1.0)), (5.0, Scale(scale = 60.0)), (2.0, Scale(scale = 1.0))],))    

    # Duplicate Scales
    cases.append(("2 minutos y 3 minutos, 5 minutos", True, 600.0, [], [(2.0, Scale(scale = 60.0)), (3.0, Scale(scale = 60.0)), (5.0, Scale(scale = 60.0))],))
    cases.append(("dos mil cinco segundos, veinte mil segundos", True, 22005.0, [], [(2005.0, Scale(scale = 1.0)), (20000.0, Scale(scale = 1.0))],))
    cases.append(("dos mil cinco, veinte mil segundos", True, 20000.0, [(2005.0, FailureFlags.CONSECUTIVE_VALUE)], [(20000.0, Scale(scale = 1.0))],))
    
    return cases


def generate_strict_tests():
    cases = []
    # Basic Functionality
    cases.append(("", False, 0.0, [], [],))
    cases.append(("AHHHHH, \u00BFque???###", False, 0.0, [("AHHHHH", FailureFlags.UNKNOWN_TERM), ("que", FailureFlags.UNKNOWN_TERM), ("?", FailureFlags.CONSECUTIVE_SPECIAL), ("?", FailureFlags.CONSECUTIVE_SPECIAL), ("###", FailureFlags.UNKNOWN_TERM)], [],))
    cases.append(("0", True, 0.0, [], [(0.0, Scale(scale = 1.0))],))
    cases.append(("5 segundos", True, 5.0, [], [(5.0, Scale(scale = 1.0))],))
    cases.append(("5 segundos 3", False, 5.0, [(3.0, FailureFlags.LONELY_VALUE)], [(5.0, Scale(scale = 1.0))],))
    for decimal in Spanish()._decimal_delimiters:
        cases.append((f"5{decimal}5 segundos", True, 5.5, [], [(5.5, Scale(scale = 1.0))],))
    for thousand in Spanish()._thousand_delimiters:
        cases.append((f"5{thousand}500 segundos", True, 5500.0, [], [(5500.0, Scale(scale = 1.0))],))
    for thousand in Spanish()._thousand_delimiters:
        for decimal in Spanish()._decimal_delimiters:
            cases.append((f"5{thousand}500{decimal}55 segundos", True, 5500.55, [], [(5500.55, Scale(scale = 1.0))],))
    cases.append(("1h5m30s", True, 3930.0, [], [(1.0, Scale(scale = 3600.0)), (5.0, Scale(scale = 60.0)), (30.0, Scale(scale = 1.0))],))
    cases.append(("1 hora 5 minutos 30 segundos", True, 3930.0, [], [(1.0, Scale(scale = 3600.0)), (5.0, Scale(scale = 60.0)), (30.0, Scale(scale = 1.0))],))
    cases.append(("1 hora 5min30s", True, 3930.0, [], [(1.0, Scale(scale = 3600.0)), (5.0, Scale(scale = 60.0)), (30.0, Scale(scale = 1.0))],))

    # Segmentors as of Writing: "," "y" "&"
    cases.append(("1 hora, 5 minutos, y 30 segundos & 7ms", True, 3930.007, [], [(1.0, Scale(scale = 3600.0)), (5.0, Scale(scale = 60.0)), (30.0, Scale(scale = 1.0)), (7.0, Scale(scale = 0.001))],))
    cases.append(("5m,, 5s", False, 305.0, [(",", FailureFlags.CONSECUTIVE_SEGMENTOR)], [(5.0, Scale(scale = 60.0)), (5.0, Scale(scale = 1.0))],))
    cases.append(("1, 2, 3 minutos", True, 360.0, [], [(6.0, Scale(scale = 60.0))],))
    # Connectors as of Writing: " ", "-", "\t"
    cases.append(("1 minuto-2-segundos	3MS", True, 62.003, [], [(1.0, Scale(scale = 60.0)), (2.0, Scale(scale = 1.0)), (3.0, Scale(scale = 0.001))],))
    cases.append(("5m,   5s", False, 305.0, [(" ", FailureFlags.CONSECUTIVE_CONNECTOR)], [(5.0, Scale(scale = 60.0)), (5.0, Scale(scale = 1.0))],))

    # Numerals / Modifiers / Multipliers
    cases.append(("cero", True, 0.0, [], [(0.0, Scale(scale = 1.0))],))
    cases.append(("cero minutos", True, 0.0, [], [(0.0, Scale(scale = 60.0))],))
    cases.append(("cinco", True, 5.0, [], [(5.0, Scale(scale = 1.0))],))

    cases.append(("un mil", True, 1000.0, [], [(1000.0, Scale(scale = 1.0))],))
    cases.append(("un mil y cinco", True, 1005.0, [], [(1005.0, Scale(scale = 1.0))],))
    cases.append(("un mil segundos y cinco", False, 1000.0, [(5.0, FailureFlags.LONELY_VALUE)], [],))

    cases.append(("medio", True, 0.5, [], [(0.5, Scale(scale = 1.0))],))
    cases.append(("medio min", True, 30.0, [], [(0.5, Scale(scale = 60.0))],))
    cases.append(("veintitrés de medio min", True, 690, [], [(11.5, Scale(scale = 60))],))
    cases.append(("veintitrés medio de min", True, 690, [], [(11.5, Scale(scale = 60))],))
    cases.append(("medio de veintitrés min", True, 690, [], [(11.5, Scale(scale = 60))],))
    cases.append(("medio veintitrés min", True, 690, [], [(11.5, Scale(scale = 60))],))
    cases.append(("medio medio veintitrés min", True, 345, [], [(5.75, Scale(scale = 60))],))
    cases.append(("medio de medio de veintitrés min", True, 345, [], [(5.75, Scale(scale = 60))],))
    cases.append(("medio de medio veintitrés min", True, 345, [], [(5.75, Scale(scale = 60))],))
    cases.append(("medio medio de veintitrés min", True, 345, [], [(5.75, Scale(scale = 60))],))
    cases.append(("veintitrés de medio medio mins", True, 345, [], [(5.75, Scale(scale = 60))],))
    cases.append(("veintitrés medio medio de min", True, 345, [], [(5.75, Scale(scale = 60))],))
    cases.append(("un millón de segundos medio", False, 1000000.0, [(0.5, FailureFlags.LONELY_VALUE)], [(1000000.0, Scale(scale = 1.0))],))
    cases.append(("un millón de segundos medio de", False, 1000000.0, [("de", FailureFlags.UNUSED_MULTIPLIER), (0.5, FailureFlags.LONELY_VALUE)], [(1000000.0, Scale(scale = 1.0))],))

    cases.append(("veintidos seg", True, 22.0, [], [(22.0, Scale(scale = 1.0))],))
    cases.append(("mil segundos", True, 1000.0, [], [(1000.0, Scale(scale = 1.0))],))
    cases.append(("un millon segundos", True, 1000000.0, [], [(1000000.0, Scale(scale = 1.0))],))
    cases.append(("medio de millon segundos", True, 500000.0, [], [(500000.0, Scale(scale = 1.0))],))
    cases.append(("medio millon segundos", True, 500000.0, [], [(500000.0, Scale(scale = 1.0))],))
    cases.append(("un tercio de mil millon de segundos", True, 333333333.3333333, [], [(333333333.3333333, Scale(scale = 1.0))],))
    cases.append(("un millon medio de segundos", True, 500000.0, [], [(500000.0, Scale(scale = 1.0))],))
    cases.append(("un millon de medio segundos", True, 500000.0, [], [(500000.0, Scale(scale = 1.0))],))
    cases.append(("una mitad de minutos", True, 30.0, [], [(0.5, Scale(scale = 60.0))],))
    cases.append(("una mitad minutos de ", False, 30.0, [("de", FailureFlags.UNUSED_MULTIPLIER)], [(0.5, Scale(scale = 60.0))],))
    cases.append(("la mitad de un millon seg", True, 500000.0, [], [(500000.0, Scale(scale = 1.0))],))
    cases.append(("dos mil quinientos minutos y medio de un millón doscientos cincuenta y seis mil segundos", True, 778000.0, [], [(2500.0, Scale(scale = 60.0)), (628000.0, Scale(scale = 1.0))],))
    
    cases.append((f"dos de seis minutos", True, 720.0, [], [(12.0, Scale(scale = 60.0))],))
    cases.append((f"2 de seis minutos", True, 720.0, [], [(12.0, Scale(scale = 60.0))],))
    cases.append((f"dos de 6 minutos", True, 720.0, [], [(12.0, Scale(scale = 60.0))],))
    cases.append((f"2 de", False, 0.0, [(f"de", FailureFlags.UNUSED_MULTIPLIER), (2.0, FailureFlags.LONELY_VALUE)], [],))

    # Numeral Type Combinations + Float/Numeral Combinations
    cases.append(("CINCO horas, 2 minutos, 3s", True, 18123.0, [], [(5.0, Scale(scale = 3600.0)), (2.0, Scale(scale = 60.0)), (3.0, Scale(scale = 1.0))],))
    cases.append(("1 2 segundos", False, 2.0, [(1.0, FailureFlags.CONSECUTIVE_VALUE)], [(2.0, Scale(scale = 1.0))],))
    cases.append(("un dos segundos", True, 12.0, [], [(12.0, Scale(scale = 1.0))],))
    cases.append(("1 dos segundos", False, 2.0, [(1.0, FailureFlags.CONSECUTIVE_VALUE)], [(2.0, Scale(scale = 1.0))],))
    cases.append(("un 2 segundos", False, 2.0, [(1.0, FailureFlags.CONSECUTIVE_VALUE)], [(2.0, Scale(scale = 1.0))],))

    cases.append(("1 13 segundos", False, 13.0, [(1.0, FailureFlags.CONSECUTIVE_VALUE)], [(13.0, Scale(scale = 1.0))],))
    cases.append(("un trece segundos", True, 113.0, [], [(113.0, Scale(scale = 1.0))],))
    cases.append(("1 trece segundos", False, 13.0, [(1.0, FailureFlags.CONSECUTIVE_VALUE)], [(13.0, Scale(scale = 1.0))],))
    cases.append(("un 13 segundos", False, 13.0, [(1.0, FailureFlags.CONSECUTIVE_VALUE)], [(13.0, Scale(scale = 1.0))],))

    cases.append(("1 50 segundos", False, 50.0, [(1.0, FailureFlags.CONSECUTIVE_VALUE)], [(50.0, Scale(scale = 1.0))],))
    cases.append(("un cincuenta segundos", True, 150.0, [], [(150.0, Scale(scale = 1.0))],))
    cases.append(("1 cincuenta segundos", False, 50.0, [(1.0, FailureFlags.CONSECUTIVE_VALUE)], [(50.0, Scale(scale = 1.0))],))
    cases.append(("un 50 segundos", False, 50.0, [(1.0, FailureFlags.CONSECUTIVE_VALUE)], [(50.0, Scale(scale = 1.0))],))

    cases.append(("3 100 segundos", True, 3100.0, [], [(3100.0, Scale(scale = 1.0))],))
    cases.append(("tres cien segundos", True, 300.0, [], [(300.0, Scale(scale = 1.0))],))
    cases.append(("3 cien segundos", True, 300.0, [], [(300.0, Scale(scale = 1.0))],))
    cases.append(("tres 100 segundos", False, 100.0, [(3.0, FailureFlags.CONSECUTIVE_VALUE)], [(100.0, Scale(scale = 1.0))],))
    cases.append(("tres un cien segundos", True, 3100.0, [], [(3100.0, Scale(scale = 1.0))],))
    cases.append(("tres 1 cien segundos", False, 100.0, [(3.0, FailureFlags.CONSECUTIVE_VALUE)], [(100.0, Scale(scale = 1.0))],))
    cases.append(("3 un cien segundos", False, 100.0, [(3.0, FailureFlags.CONSECUTIVE_VALUE)], [(100.0, Scale(scale = 1.0))],))

    cases.append(("15 5 segundos", False, 5.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(5.0, Scale(scale = 1.0))],))
    cases.append(("quince cinco segundos", False, 5.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(5.0, Scale(scale = 1.0))],))
    cases.append(("15 cinco segundos", False, 5.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(5.0, Scale(scale = 1.0))],))
    cases.append(("quince 5 segundos", False, 5.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(5.0, Scale(scale = 1.0))],))

    cases.append(("15 15 segundos", False, 15.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(15.0, Scale(scale = 1.0))],))
    cases.append(("quince quince segundos", True, 1515.0, [], [(1515.0, Scale(scale = 1.0))],))
    cases.append(("15 quince segundos", False, 15.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(15.0, Scale(scale = 1.0))],))
    cases.append(("quince 15 segundos", False, 15.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(15.0, Scale(scale = 1.0))],))

    cases.append(("15 20 segundos", False, 20.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(20.0, Scale(scale = 1.0))],))
    cases.append(("quince veinte segundos", True, 1520.0, [], [(1520.0, Scale(scale = 1.0))],))
    cases.append(("15 veinte segundos", False, 20.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(20.0, Scale(scale = 1.0))],))
    cases.append(("quince 20 segundos", False, 20.0, [(15.0, FailureFlags.CONSECUTIVE_VALUE)], [(20.0, Scale(scale = 1.0))],))

    cases.append(("20 1 segundos", False, 1.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE)], [(1.0, Scale(scale = 1.0))],))
    cases.append(("veinte un segundos", True, 21.0, [], [(21.0, Scale(scale = 1.0))],))
    cases.append(("20 un segundos", False, 1.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE)], [(1.0, Scale(scale = 1.0))],))
    cases.append(("veinte 1 segundos", False, 1.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE)], [(1.0, Scale(scale = 1.0))],))

    cases.append(("20 15 segundos", False, 15.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE)], [(15.0, Scale(scale = 1.0))],))
    cases.append(("veinte quince segundos", True, 2015.0, [], [(2015.0, Scale(scale = 1.0))],))
    cases.append(("20 quince segundos", False, 15.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE)], [(15.0, Scale(scale = 1.0))],))
    cases.append(("veinte 15 segundos", False, 15.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE)], [(15.0, Scale(scale = 1.0))],))

    cases.append(("20 30 segundos", False, 30.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE)], [(30.0, Scale(scale = 1.0))],))
    cases.append(("veinte treinta segundos", True, 2030.0, [], [(2030.0, Scale(scale = 1.0))],))
    cases.append(("20 treinta segundos", False, 30.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE)], [(30.0, Scale(scale = 1.0))],))
    cases.append(("veinte 30 segundos", False, 30.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE)], [(30.0, Scale(scale = 1.0))],))
    cases.append(("veinte veinte tres segundos", True, 2023.0, [], [(2023.0, Scale(scale = 1.0))],))
    cases.append(("veinte 20 tres segundos", False, 3.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE), (20.0, FailureFlags.CONSECUTIVE_VALUE)], [(3.0, Scale(scale = 1.0))],))
    cases.append(("veinte 20 3 segundos", False, 3.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE), (20.0, FailureFlags.CONSECUTIVE_VALUE)], [(3.0, Scale(scale = 1.0))],))
    cases.append(("veinte 20 3", False, 0.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE), (20.0, FailureFlags.CONSECUTIVE_VALUE), (3.0, FailureFlags.LONELY_VALUE)], [],))
    cases.append(("1 minuto segundos", False, 60.0, [("segundos", FailureFlags.CONSECUTIVE_SCALE)], [(1.0, Scale(scale = 60.0))],))
    cases.append(("minuto 1 segundos", False, 1.0, [("minuto", FailureFlags.LEADING_SCALE)], [(1.0, Scale(scale = 1.0))],))
    
    # Long Numerals + Segmentor Combinations
    cases.append(("veintitrés mil seg", True, 23000.0, [], [(23000.0, Scale(scale = 1.0))],))
    cases.append(("dos mil veintitrés seg", True, 2023.0, [], [(30.0, Scale(scale = 1.0))],))
    cases.append(("dos mil veintitrés cinco seg", False, 5.0, [(2023.0, FailureFlags.CONSECUTIVE_VALUE)], [(5.0, Scale(scale = 1.0))],))
    cases.append(("dos mil veintitrés mil cinco seg", False, 23005.0, [(2000.0, FailureFlags.LONELY_VALUE)], [(23005.0, Scale(scale = 1.0))],))
    cases.append(("dos mil veintitrés cinco segundos", False, 5.0, [(2023.0, FailureFlags.CONSECUTIVE_VALUE)], [(5.0, Scale(scale = 1.0))],))
    cases.append(("un mil cinco y cien", True, 1500.0, [], [(1500.0, Scale(scale = 1.0))],))
    cases.append(("un mil 5 y cien", True, 1500.0, [], [(1500.0, Scale(scale = 1.0))],))

    cases.append(("ciento setenta dos mil", True, 172000.0, [], [(172000.0, Scale(scale = 1.0))],))
    cases.append(("ciento setenta y dos mil", True, 172000.0, [], [(172000.0, Scale(scale = 1.0))],))
    cases.append(("un millón setenta dos mil", True, 1072000.0, [], [(1072000.0, Scale(scale = 1.0))],))
    cases.append(("un millón y setenta dos mil", True, 1072000.0, [], [(1072000.0, Scale(scale = 1.0))],))
    cases.append(("setenta dos mil quinientos y seis", True, 72506.0, [], [(72506.0, Scale(scale = 1.0))],))
    cases.append(("un millón setenta y dos mil quinientos seis", True, 1072506.0, [], [(1072506.0, Scale(scale = 1.0))],))
    cases.append(("un millón setenta dos mil quinientos y seis millones", True, 1072506000000.0, [], [(1072506000000.0, Scale(scale = 1.0))],))

    # Awkward Thousands/Decimals
    cases.append(("veinte,18 tres segundos", False, 3.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE), (18.0, FailureFlags.CONSECUTIVE_VALUE)], [(3.0, Scale(scale = 1.0))],))
    cases.append(("veinte ,18 tres segundos", False, 3.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE), (0.18, FailureFlags.CONSECUTIVE_VALUE)], [(3.0, Scale(scale = 1.0))],))
    cases.append(("veinte 18 tres segundos", False, 3.0, [(20.0, FailureFlags.CONSECUTIVE_VALUE), (18.0, FailureFlags.CONSECUTIVE_VALUE)], [(3.0, Scale(scale = 1.0))],))
    
    # HHMMSS + Combinations
    cases.append(("12:30:15,25", True, 45015.25, [], [(12.0, Scale(scale = 3600.0)), (30.0, Scale(scale = 60.0)), (15.25, Scale(scale = 1.0))],))
    cases.append(("22: 5", True, 1325.0, [], [(22.0, Scale(scale = 60.0)), (5.0, Scale(scale = 1.0))],))
    cases.append(("1:2:22:33 558:66:77,1234", True, 126558437.1234, [], [(1.0, Scale(scale = 2635200.0)), (2.0, Scale(scale = 604800.0)), (22.0, Scale(scale = 86400.0)), (33558.0, Scale(scale = 3600.0)), (66.0, Scale(scale = 60.0)), (77.1234, Scale(scale = 1.0))],))
    cases.append(("1 dia 2:30:15,25", True, 95415.25, [], [(1.0, Scale(scale = 86400.0)), (2.0, Scale(scale = 3600.0)), (30.0, Scale(scale = 60.0)), (15.25, Scale(scale = 1.0))],))
    cases.append(("22: 2.455: 5555", True, 232055.0, [], [(22.0, Scale(scale = 3600.0)), (2455.0, Scale(scale = 60.0)), (5555.0, Scale(scale = 1.0))],))
    cases.append(("22:  +2.455: 5555", False, 0.0, [("22:  +2.455: 5555", FailureFlags.MALFORMED_HHMMSS)], [],))
    cases.append(("22: 2.455 : 5555", False, 0.0, [("22: 2.455 : 5555", FailureFlags.MALFORMED_HHMMSS)], [],))
    cases.append(("22: 2.455 5: 5555", False, 3775.0, [("5: 5555", FailureFlags.DUPLICATE_SCALE)], [(22.0, Scale(scale = 60.0)), (2455.0, Scale(scale = 1.0))],))
    cases.append(("22: 2 455: +5555", True, 232055.0, [], [(22.0, Scale(scale = 3600.0)), (2455.0, Scale(scale = 60.0)), (5555.0, Scale(scale = 1.0))],))
    cases.append(("22: 2.455: ++5555", False, 0.0, [("22: 2.455: ++5555", FailureFlags.MALFORMED_HHMMSS)], [],))
    cases.append(("2:55 5 minutos", False, 175.0, [("5 minutos", FailureFlags.DUPLICATE_SCALE)], [(2.0, Scale(scale = 60.0)), (55.0, Scale(scale = 1.0))],))
    cases.append(("2: 6 5: 2", False, 126.0, [("5: 2", FailureFlags.DUPLICATE_SCALE)], [(2.0, Scale(scale = 60.0)), (6.0, Scale(scale = 1.0))],))
    
    # Duplicate Scales
    cases.append(("2 minutos y 3 minutos, 5 minutos", False, 120.0, [("3 minutos", FailureFlags.DUPLICATE_SCALE), ("5 minutos", FailureFlags.DUPLICATE_SCALE)], [(2.0, Scale(scale = 60.0))],))
    cases.append(("dos mil cinco segundos, veinte mil segundos", False, 2005.0, [("veinte mil segundos", FailureFlags.DUPLICATE_SCALE)], [(2005.0, Scale(scale = 1.0))],))
    cases.append(("dos mil cinco, veinte mil segundos", False, 20000.0, [(2005.0, FailureFlags.CONSECUTIVE_VALUE)], [(20000.0, Scale(scale = 1.0))],))
    
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
