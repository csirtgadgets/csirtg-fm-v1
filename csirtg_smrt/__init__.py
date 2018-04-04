#!/usr/bin/env python

import logging
import os.path
import textwrap
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from pprint import pprint
import sys
import select

from csirtg_smrt.constants import SMRT_RULES_PATH
from csirtg_smrt.rule import Rule
from csirtg_smrt.utils import setup_logging, get_argument_parser, load_plugin, setup_signals, \
    setup_runtime_path, chunk
from csirtg_smrt.exceptions import RuleUnsupported
from csirtg_indicator.utils import resolve_itype
from csirtg_indicator.exceptions import InvalidIndicator

# http://python-3-patterns-idioms-test.readthedocs.org/en/latest/Factory.html
# https://gist.github.com/pazdera/1099559
logging.getLogger("requests").setLevel(logging.WARNING)

if os.getenv('CSIRTG_SMRT_HTTP_TRACE', '0') == '0':
    logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class Smrt(object):

    def __init__(self, **kwargs):
        pass

    def _load_rules_dir(self, rule):
        for f in sorted(os.listdir(rule)):
            if f.startswith('.'):
                continue

            if os.path.isdir(f):
                continue

            logger.info("processing {0}/{1}".format(rule, f))

            try:
                r = Rule(path=os.path.join(rule, f))
            except RuleUnsupported as e:
                logger.error(e)
                continue

            for feed in r.feeds:
                yield r, feed

    def load_rules(self, rule, feed=None):
        if os.path.isdir(rule):
            return self._load_feeds_dir(rule)

        logger.info("processing {0}".format(rule))
        try:
            rule = Rule(path=rule)
        except Exception as e:
            logger.error(e)

        if feed:
            # replace the feeds dict with the single feed
            # raises KeyError if it doesn't exist
            rule.feeds = {feed: rule.feeds[feed]}

        for f in rule.feeds:
            yield rule, f

    def load_parser(self, parser_name):
        plugin_path = os.path.join(os.path.dirname(__file__), 'parsers')
        return load_plugin(plugin_path, parser_name)

    def is_valid(self, i):
        try:
            resolve_itype(i.indicator)
            return True
        except InvalidIndicator as e:
            if logger.getEffectiveLevel() == logging.DEBUG:
                if not self.skip_invalid:
                    raise e
            return False

    def process(self, rule, feed, parser_name, cli):
        parser = self.load_parser(parser_name)
        parser = parser.Plugin(rule=rule, feed=feed, cache=cli.cache)

        indicators = parser.process()
        indicators = (i for i in indicators if self.is_valid(i))

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

    p.add_argument("-r", "--rule", help="specify the rules directory or specific rules file [default: %(default)s",
                   default=SMRT_RULES_PATH)

    p.add_argument("-f", "--feed", help="specify the feed to process")

    p.add_argument("--limit", help="limit the number of records processed [default: %(default)s]",
                   default=None)

    p.add_argument('--no-fetch', help='do not re-fetch if the cache exists', action='store_true')
    p.add_argument('--no-verify-ssl', help='turn TLS/SSL verification OFF', action='store_true')

    p.add_argument('--skip-invalid', help="skip invalid indicators in DEBUG (-d) mode", action="store_true")
    p.add_argument('--skip-broken', help='skip seemingly broken feeds', action='store_true')

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

    for r, f in s.load_rules(args.rule, feed=args.feed):
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
        logger.info('processing: {} - {}:{}'.format(args.rule, r.defaults['provider'], f))
        try:
            for i in s.process(r, f, parser_name, cli):
                if i:
                    indicators.append(i)

        except Exception as e:
            logger.error(e)
            import traceback
            traceback.print_exc()

    pprint(indicators)


if __name__ == "__main__":
    main()
