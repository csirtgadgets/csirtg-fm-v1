from csirtg_fm import FM
from csirtg_fm.rule import Rule
from csirtg_fm.utils.content import get_type

rule = 'test/openphish/openphish.yml'
rule = Rule(path=rule)
s = FM()


def test_openphish():
    indicators = []

    from csirtg_fm.clients.http import Client
    cli = Client(rule, 'urls')

    parser_name = get_type(cli.cache)
    assert parser_name == 'csv'

    for i in s.process(rule, 'urls', parser_name, cli, limit=25, indicators=[]):
        if not i:
            continue

        indicators.append(i)

    assert len(indicators) > 0
    assert len(indicators[0].indicator) > 4