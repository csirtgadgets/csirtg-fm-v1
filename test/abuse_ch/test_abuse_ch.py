
from csirtg_fm import FM
from csirtg_fm.rule import Rule
from csirtg_fm.utils.content import get_type

rule = 'test/abuse_ch/abuse_ch.yml'
rule = Rule(path=rule)
s = FM()


def test_abuse_ch_urlhaus():
    indicators = set()
    tags = set()

    from csirtg_fm.clients.http import Client
    cli = Client(rule, 'urlhaus')

    parser_name = get_type(cli.cache)
    assert parser_name == 'csv'

    for i in s.process(rule, 'urlhaus', parser_name, cli, limit=250):
        if not i:
            continue

        indicators.add(i.indicator)
        tags.add(i.tags[0])

    from pprint import pprint
    pprint(indicators)
    assert 'http://business.imuta.ng/default/US/Summit-Companies-Invoice-12648214'.lower() in indicators
    assert 'exploit' in tags
