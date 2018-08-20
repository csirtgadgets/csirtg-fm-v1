from csirtg_fm import FM
from csirtg_fm.rule import Rule

rule = 'test/openphish/openphish.yml'
rule = Rule(path=rule)
s = FM()


def test_openphish():
    indicators = []

    from csirtg_fm.clients.http import Client
    cli = Client(rule, 'urls')

    for i in s.process(rule, 'urls', 'pattern', cli, limit=25, indicators=[]):
        if not i:
            continue

        indicators.append(i)

    assert len(indicators) > 0
    assert len(indicators[0].indicator) > 4