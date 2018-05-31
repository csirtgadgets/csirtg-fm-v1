import py.test

from csirtg_fm import FM
from csirtg_fm.rule import Rule, load_rules
from csirtg_fm.clients.http import Client
from csirtg_fm.utils.content import get_type
from pprint import pprint
rule = 'examples/csirtg.yml'


def test_csirtg_darknet():
    feed = 'csirtgadgets/darknet'
    r, f = next(load_rules(rule, feed))

    r.feeds[feed]['remote'] = 'test/csirtg/feed.txt'

    cli = Client(r, f)
    s = FM(client='stdout')

    parser_name = get_type(cli.cache)

    x = list(s.process(r, f, parser_name, cli))

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
