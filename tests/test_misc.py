import pytest

from timelength.locales import English
from timelength.timelength import TimeLength


@pytest.fixture
def tl_notstrict():
    return TimeLength(content = "0 seconds", locale = English())


def test_parsedtimelength_reset(tl_notstrict):
    tl_notstrict.content = "5 seconds"
    tl_notstrict.parse()
    first_seconds = tl_notstrict.result.seconds
    tl_notstrict.content = "7 seconds"
    tl_notstrict.parse()
    second_seconds = tl_notstrict.result.seconds
    assert first_seconds != second_seconds
