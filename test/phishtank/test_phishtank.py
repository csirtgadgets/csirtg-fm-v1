from csirtg_fm import FM
from csirtg_fm.rule import Rule
from csirtg_fm.utils.content import get_type
from csirtg_indicator.utils import parse_timestamp

rule = 'test/phishtank/phishtank.yml'
rule = Rule(path=rule)
s = FM()


def test_phishtank_urls():
    indicators = set()
    tags = set()

    from csirtg_fm.clients.http import Client
    cli = Client(rule, 'urls')
    cli._cache_decode()
    cli.cache = 'test/phishtank/feed.json'

    parser_name = get_type(cli.cache)
    assert parser_name == 'json'

    for i in s.process(rule, 'urls', parser_name, cli):
        if not i:
            continue

        assert parse_timestamp(i.reported_at).year > 1980
        assert parse_timestamp(i.last_at).year > 1980
        assert parse_timestamp(i.first_at).year > 1980

        indicators.add(i.indicator)
        tags.add(i.tags[0])

    assert 'http://charlesleonardconstruction.com/irs/confim/index.html' in indicators
