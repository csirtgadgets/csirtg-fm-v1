import py.test

from csirtg_smrt import Smrt
from csirtg_smrt.rule import Rule

rule = 'test/csirtg/csirtg.yml'
rule = Rule(path=rule)
rule.fetcher = 'file'


def test_csirtg_darknet():
    feed = 'darknet'
    cli = Client(rule, feed)
    s = Smrt(cli)
    rule.feeds[feed]['remote'] = 'test/csirtg/feed.txt'
    x = s.process(rule, feed=feed)
    x = list(x)
    assert len(x) > 0

    ips = set()
    tags = set()

    for xx in x:
        ips.add(xx.indicator)
        tags.add(xx.tags[0])

    assert '109.111.134.64' in ips
    assert 'scanner' in tags


def test_csirtg_skips():
    rule.feeds['darknet']['remote'] = 'test/csirtg/feed.txt'
    rule.skip = '216.121.233.27'

    x = s.process(rule, feed="darknet")
    x = list(x)
    assert len(x) > 0

    ips = set()

    for xx in x:
        ips.add(xx.indicator)

    assert '216.121.233.27' not in ips

    ips = set()

    rule.skip = None
    rule.feeds['darknet']['skip'] = '216.121.233.27'

    x = s.process(rule, feed="darknet")
    x = list(x)
    assert len(x) > 0

    ips = set()

    for xx in x:
        ips.add(xx.indicator)

    assert '216.121.233.27' not in ips
