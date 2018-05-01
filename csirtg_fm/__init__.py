#!/usr/bin/env python3

import logging
import os.path
import textwrap
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from pprint import pprint
import sys
import select
import arrow
import itertools
from time import sleep

from csirtg_indicator.utils import resolve_itype, normalize_itype
from csirtg_indicator.format import FORMATS
from csirtg_indicator.constants import COLUMNS
from csirtg_indicator import Indicator

from csirtg_fm.constants import FM_RULES_PATH, CACHE_PATH
from csirtg_fm.rule import Rule
from csirtg_fm.utils import setup_logging, get_argument_parser, load_plugin, setup_signals, setup_runtime_path, chunk
from csirtg_fm.exceptions import RuleUnsupported
from csirtg_fm.constants import FIREBALL_SIZE
from csirtg_fm.utils.content import get_type
from .rule import load_rules
from .archiver import Archiver, NOOPArchiver

FORMAT = os.getenv('CSIRTG_FM_FORMAT', 'table')
STDOUT_FIELDS = COLUMNS
ARCHIVE_PATH = os.environ.get('CSIRTG_SMRT_ARCHIVE_PATH', CACHE_PATH)
ARCHIVE_PATH = os.path.join(ARCHIVE_PATH, 'fm.db')
GOBACK_DAYS = 3

# http://python-3-patterns-idioms-test.readthedocs.org/en/latest/Factory.html
# https://gist.github.com/pazdera/1099559
logging.getLogger("requests").setLevel(logging.WARNING)

if os.getenv('CSIRTG_FM_HTTP_TRACE', '0') == '0':
    logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class FM(object):

    def __init__(self, **kwargs):
        self.archiver = kwargs.get('archiver', NOOPArchiver())
        self.goback = kwargs.get('goback')
        self.skip_invalid = kwargs.get('skip_invalid')
        self.client = kwargs.get('client')

        if self.client and self.client != 'stdout':
            self._init_client()

    def _init_client(self):
        if self.client != 'stdout':
            plugin_path = os.path.join(os.path.dirname(__file__), 'clients')
            print(plugin_path)
            c = load_plugin(plugin_path, self.client)
            if not c:
                raise RuntimeError("Unable to load plugin: {}".format(c))

            self.client = c.Plugin()

    def is_valid(self, i):
        try:
            resolve_itype(i['indicator'])
        except TypeError as e:
            if logger.getEffectiveLevel() == logging.DEBUG:
                if not self.skip_invalid:
                    raise e
            return False

        return True

    def is_old(self, i):
        if i.last_at and i.last_at < self.goback:
            return True

    # silver-meme?
    def clean_indicator(self, i):
        if isinstance(i, dict):
            i = Indicator(**i)

        if not i.first_at:
            i.first_at = i.last_at

        if not i.reported_at:
            i.reported_at = arrow.utcnow().datetime

        if not i.group:
            i.group = 'everyone'

        if not i.tlp:
            i.tlp = 'white'

        if i.confidence:
            return i

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

    def is_archived(self, i):
        if isinstance(self.archiver, NOOPArchiver):
            return

        if self.archiver.search(i):
            logger.debug('skipping: {}/{}/{}/{}'.format(i.indicator, i.provider, i.first_at, i.last_at))
            return True

        logger.debug('adding: {}/{}/{}/{}'.format(i.indicator, i.provider, i.first_at, i.last_at))

    def fetch_csirtg(self, f, limit=250):
        from .clients.csirtg import Client
        cli = Client()
        user, feed = f.split('/')
        return cli.fetch(user, feed, limit=limit)

    def process(self, rule, feed, parser_name, cli, limit=None, indicators=[]):

        if parser_name != 'csirtg':
            # detect and load the parser
            plugin_path = os.path.join(os.path.dirname(__file__), 'parsers')
            parser = load_plugin(plugin_path, parser_name)
            parser = parser.Plugin(rule=rule, feed=feed, cache=cli.cache)

            # bring up the pipeline
            indicators = parser.process()

        indicators = (i for i in indicators if self.is_valid(i))
        indicators = (self.clean_indicator(i) for i in indicators)

        # check to see if the indicator is too old
        if self.goback:
            indicators = (i for i in indicators if not self.is_old(i))

        if not limit:
            limit = rule.feeds[feed].get('limit')

        if limit:
            indicators = itertools.islice(indicators, int(limit))

        indicators = (i for i in indicators if not self.is_archived(i))

        indicators_batches = chunk(indicators, int(FIREBALL_SIZE))
        for batch in indicators_batches:
            # send batch
            if self.client and self.client != 'stdout':
                self.client.indicators_create(batch)

            # archive
            self.archiver.begin()
            for i in batch:
                yield i.format_keys()
                self.archiver.create(i)

            # commit
            self.archiver.commit()


def main():
    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
        Env Variables:
            CSIRTG_RUNTIME_PATH
            

        example usage:
            $ csirtg-fm --rule rules/default
            $ csirtg-fm --rule default/csirtg.yml --feed port-scanners --remote http://localhost:5000
        '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='csirtg-fm',
        parents=[p],
    )

    p.add_argument("-r", "--rule", help="specify the rules directory or specific rules file [default: %(default)s",
                   default=FM_RULES_PATH)

    p.add_argument("-f", "--feed", help="specify the feed to process")

    p.add_argument("--limit", help="limit the number of records processed [default: %(default)s]",
                   default=None)

    p.add_argument('--no-fetch', help='do not re-fetch if the cache exists', action='store_true')
    p.add_argument('--no-verify-ssl', help='turn TLS/SSL verification OFF', action='store_true')

    p.add_argument('--skip-invalid', help="skip invalid indicators in DEBUG (-d) mode", action="store_true")
    p.add_argument('--skip-broken', help='skip seemingly broken feeds', action='store_true')

    p.add_argument('--format', help='specify output format [default: %(default)s]"', default=FORMAT,
                   choices=FORMATS)
    p.add_argument('--fields', help='specify fields for stdout [default %(default)s]"', default=','.join(STDOUT_FIELDS))

    p.add_argument('--remember-path', help='specify remember db path [default: %(default)s', default=ARCHIVE_PATH)
    p.add_argument('--remember', help='remember what has been already processed', action='store_true')

    p.add_argument('--client', default='stdout')

    p.add_argument('--goback', help='specify default number of days to start out at [default %(default)s]',
                   default=GOBACK_DAYS)

    args = p.parse_args()

    setup_logging(args)

    logger.info('loglevel is: {}'.format(logging.getLevelName(logger.getEffectiveLevel())))

    # we're running as a service
    setup_signals(__name__)
    
    logger.info('starting...')

    archiver = NOOPArchiver()
    if args.remember:
        archiver = Archiver(dbfile=args.remember_path)

    goback = args.goback
    if goback:
        goback = arrow.utcnow().replace(days=-int(goback))

    s = FM(archiver=archiver, client=args.client, goback=goback)

    data = None
    if select.select([sys.stdin, ], [], [], 0.0)[0]:
        data = sys.stdin.read()

    fetch = True
    if args.no_fetch:
        fetch = False

    data = []
    indicators = []

    for r, f in load_rules(args.rule, feed=args.feed):
        if not f:
            print("\n")
            print('Feed not found: %s' % args.feed)
            print("\n")
            raise SystemExit()

        # detect which client we should be using

        if '/' in f:
            parser_name = 'csirtg'
            cli = None
            for i in s.fetch_csirtg(f, limit=args.limit):
                data.append(i)

        else:
            from .clients.http import Client
            cli = Client(r, f)

            # fetch the feeds
            if fetch:
                cli.fetch()

            # decode the content and load the parser
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
            for i in s.process(r, f, parser_name, cli, limit=args.limit, indicators=data):
                if not i:
                    continue

                indicators.append(i)

        except Exception as e:
            logger.error(e)
            import traceback
            traceback.print_exc()

    if args.client == 'stdout':
        for l in FORMATS[args.format](data=indicators, cols=args.fields.split(',')):
            print(l)


if __name__ == "__main__":
    main()
