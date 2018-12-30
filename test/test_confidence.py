from csirtg_indicator import Indicator
from csirtg_fm.utils.confidence import estimate_confidence


def test_confidence():
    i = Indicator('128.205.1.1', tags='scanner')
    assert estimate_confidence(i) == 4

    i = Indicator('128.205.1.1')
    assert estimate_confidence(i) == 2

    i = Indicator('128.205.1.1', probability=88)
    assert estimate_confidence(i) == 4

    i = Indicator('http://go0gle.com/1.html', tags='phishing')
    assert estimate_confidence(i) == 4
