import py.test

from csirtg_fm import FM
from csirtg_fm.rule import Rule
from csirtg_fm.utils.content import get_type
from pprint import pprint

rule = 'test/malc0de/malc0de.yml'
rule = Rule(path=rule)
s = FM()


def test_malc0de_urls():
    from csirtg_fm.clients.http import Client
    cli = Client(rule, 'urls')

    parser_name = get_type(cli.cache)
    assert parser_name == 'rss'

    indicators = set()
    for i in s.process(rule, 'urls', parser_name, cli, limit=25, indicators=[]):
        if not i:
            continue

        indicators.add(i.indicator)

    assert len(indicators) > 0
    assert len(indicators.pop()) > 4
    assert 'http://url.goosai.com/down/ufffdufffd?ufffdufffdufffd?ufffdufffdbreakprisonsearchv2.7u03afu06f0ufffdufffdufffdufffdufffdufffdat25_35027.exe' in indicators


def test_malc0de_malware():
    from csirtg_fm.clients.http import Client
    cli = Client(rule, 'malware')

    parser_name = get_type(cli.cache)
    assert parser_name == 'rss'

    indicators = set()
    for i in s.process(rule, 'malware', parser_name, cli, limit=25, indicators=[]):
        if not i:
            continue

        indicators.add(i.indicator)

    pprint(indicators)

    assert '71941a88f8c895e405dd5cf665f1ef0c' in indicators
#