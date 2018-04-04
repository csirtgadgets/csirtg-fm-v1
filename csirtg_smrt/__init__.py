#!/usr/bin/env python

import logging
import os.path
import textwrap
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from pprint import pprint
import sys
import select
import arrow

from csirtg_smrt.constants import SMRT_RULES_PATH
from csirtg_smrt.rule import Rule
from csirtg_smrt.utils import setup_logging, get_argument_parser, load_plugin, setup_signals, \
    setup_runtime_path, chunk
from csirtg_smrt.exceptions import RuleUnsupported
from csirtg_indicator.utils import resolve_itype, normalize_itype
from csirtg_indicator.exceptions import InvalidIndicator
from csirtg_indicator.format import FORMATS
from csirtg_indicator.constants import COLUMNS
from csirtg_indicator import Indicator


FORMAT = os.getenv('CSIRTG_SMRT_FORMAT', 'table')
STDOUT_FIELDS = COLUMNS

# http://python-3-patterns-idioms-test.readthedocs.org/en/latest/Factory.html
# https://gist.github.com/pazdera/1099559
logging.getLogger("requests").setLevel(logging.WARNING)

if os.getenv('CSIRTG_SMRT_HTTP_TRACE', '0') == '0':
    logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class Smrt(object):

    def __init__(self, **kwargs):
        pass

    def is_valid(self, i):
        try:
            resolve_itype(i['indicator'])
            return True
        except InvalidIndicator as e:
            if logger.getEffectiveLevel() == logging.DEBUG:
                if not self.skip_invalid:
                    raise e
            return False

    def clean_indicator(self, i, rule, feed):
        if isinstance(i, dict):
            i = Indicator(**i)

        if not i.firsttime:
            i.firsttime = i.lasttime

        if not i.reporttime:
            i.reporttime = arrow.utcnow().datetime

        if not i.group:
            i.group = 'everyone'

        if not i.tlp:
            i.tlp = 'white'

        if not i.confidence:
            i.confidence = 2
            if i.tags and len(i.tags) > 1:
                i.confidence = 3

            if i.itype == 'ipv4':
                if not i.tags:
                    i.confidence = 2

                elif 'scanner' in i.tags:
                    i.confidence = 4

                elif len(i.tags) > 1:
                    i.confidence = 4

            elif i.itype == 'url' and len(i.tags) > 1:
                i.confidence = 4

            elif i.itype == 'email' and len(i.tags) > 1:
                i.confidence = 4

        return i

    def process(self, rule, feed, parser_name, cli):
        # detect and load the parser
        plugin_path = os.path.join(os.path.dirname(__file__), 'parsers')
        parser = load_plugin(plugin_path, parser_name)
        parser = parser.Plugin(rule=rule, feed=feed, cache=cli.cache)

        # bring up the pipeline
        indicators = parser.process()
        indicators = (i for i in indicators if self.is_valid(i))
        indicators = (self.clean_indicator(i, rule, feed) for i in indicators)

        indicators_batches = chunk(indicators, int(500))
        for batch in indicators_batches:
            # send batch

            # archive

            # yield
            for i in batch:
                yield i


def main():
    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
        Env Variables:
            CSIRTG_RUNTIME_PATH
            CSIRTG_SMRT_TOKEN

        example usage:
            $ csirtg-smrt --rule rules/default
            $ csirtg-smrt --rule default/csirtg.yml --feed port-scanners --remote http://localhost:5000
        '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='csirtg-smrt',
        parents=[p],
    )

    p.add_argument('--client', default='stdout')
    p.add_argument("-r", "--rule", help="specify the rules directory or specific rules file [default: %(default)s",
                   default=SMRT_RULES_PATH)

    p.add_argument("-f", "--feed", help="specify the feed to process")

    p.add_argument("--limit", help="limit the number of records processed [default: %(default)s]",
                   default=None)

    p.add_argument('--no-fetch', help='do not re-fetch if the cache exists', action='store_true')
    p.add_argument('--no-verify-ssl', help='turn TLS/SSL verification OFF', action='store_true')

    p.add_argument('--skip-invalid', help="skip invalid indicators in DEBUG (-d) mode", action="store_true")
    p.add_argument('--skip-broken', help='skip seemingly broken feeds', action='store_true')

    p.add_argument('--format', help='specify output format [default: %(default)s]"', default=FORMAT,
                   choices=FORMATS.keys())
    p.add_argument('--fields', help='specify fields for stdout [default %(default)s]"', default=','.join(STDOUT_FIELDS))

    args = p.parse_args()

    setup_logging(args)

    logger.info('loglevel is: {}'.format(logging.getLevelName(logger.getEffectiveLevel())))

    # we're running as a service
    setup_signals(__name__)
    
    logger.info('starting...')

    s = Smrt()

    data = None
    if select.select([sys.stdin, ], [], [], 0.0)[0]:
        data = sys.stdin.read()

    fetch = True
    if args.no_fetch:
        fetch = False

    indicators = []

    from .rule import load_rules

    for r, f in load_rules(args.rule, feed=args.feed):
        # detect which client we should be using
        from .clients.http import Client
        cli = Client(r, f)

        # fetch the feeds
        if fetch:
            cli.fetch()

        # decode the content and load the parser
        from csirtg_smrt.utils.content import get_type
        try:
            logger.debug('testing parser: %s' % cli.cache)
            parser_name = get_type(cli.cache)
            logger.debug('detected parser: %s' % parser_name)
        except Exception as e:
            logger.debug(e)

        if not parser_name:
            parser_name = r.feeds[f].get('parser') or r.parser or 'pattern'

        # process the indicators by passing the parser and file handle [or data]
        logger.info('processing: {} - {}:{}'.format(args.rule, r.provider, f))
        try:
            for i in s.process(r, f, parser_name, cli):
                if i:
                    indicators.append(i)

        except Exception as e:
            logger.error(e)
            import traceback
            traceback.print_exc()

    if args.client == 'stdout':
        print(FORMATS[args.format](data=indicators, cols=args.fields.split(',')))


if __name__ == "__main__":
    main()
