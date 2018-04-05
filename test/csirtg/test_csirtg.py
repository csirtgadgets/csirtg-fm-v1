import py.test

from csirtg_fm import FM
from csirtg_fm.rule import Rule, load_rules
from csirtg_fm.clients.http import Client
from pprint import pprint
rule = 'test/csirtg/csirtg.yml'


def test_csirtg_darknet():
    feed = 'darknet'
    r, f = list(load_rules(rule, feed))

    r.feeds[feed]['remote'] = 'test/csirtg/feed.txt'

    cli = Client(r, f)
    s = FM()
    x = s.process(r, f, 'pattern', cli)

    x = list(x)
    assert len(x) > 0

    ips = set()
    tags = set()

    for xx in x:
        ips.add(xx.indicator)
        tags.add(xx.tags[0])

    assert '109.111.134.64' in ips
    assert 'scanner' in tags


# def test_csirtg_skips():
#     rule.feeds['darknet']['remote'] = 'test/csirtg/feed.txt'
#     rule.skip = '216.121.233.27'
#
#     x = s.process(rule, feed="darknet")
#     x = list(x)
#     assert len(x) > 0
#
#     ips = set()
#
#     for xx in x:
#         ips.add(xx.indicator)
#
#     assert '216.121.233.27' not in ips
#
#     ips = set()
#
#     rule.skip = None
#     rule.feeds['darknet']['skip'] = '216.121.233.27'
#
#     x = s.process(rule, feed="darknet")
#     x = list(x)
#     assert len(x) > 0
#
#     ips = set()
#
#     for xx in x:
#         ips.add(xx.indicator)
#
#     assert '216.121.233.27' not in ips
