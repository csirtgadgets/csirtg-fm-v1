#!/usr/bin/env python3

import logging
import os.path
import arrow
from pprint import pprint
import itertools

from csirtg_urlsml_tf import predict as predict_url
from csirtg_domainsml_tf import predict as predict_fqdn
from csirtg_ipsml import predict as predict_ip

from csirtg_indicator.utils import resolve_itype
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
        self.ml = kwargs.get('ml')

        if self.client and self.client != 'stdout':
            self._init_client()

        if logger.getEffectiveLevel() != logging.DEBUG:
            self.skip_invalid = True

    def _init_client(self):
        if self.client != 'stdout':
            plugin_path = os.path.join(os.path.dirname(__file__), 'clients')
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

        if not i.reported_at:
            i.reported_at = arrow.utcnow().datetime

        if not i.group:
            i.group = 'everyone'

        if not i.tlp:
            i.tlp = 'white'

        return i

    def confidence(self, i):
        if i.confidence:
            return i

        i.confidence = 2
        if i.tags and len(i.tags) > 1:
            i.confidence = 3

        if i.itype in ['md5', 'sha1', 'sha256', 'sha512']:
            i.confidence = 4
            return i

        if i.itype == 'ipv4':
            if not i.tags:
                i.confidence = 2

            elif 'scanner' in i.tags:
                i.confidence = 4

            elif len(i.tags) > 1:
                i.confidence = 4

        elif i.itype == 'url' and len(i.tags) > 1 or 'phishing' in i.tags:
            i.confidence = 4

        elif i.itype == 'email' and len(i.tags) > 1:
            i.confidence = 4

        if i.probability and i.probability >= 84:
            i.confidence = 4

        return i

    def predict_urls(self, indicators):
        indicators = list(indicators)
        urls = [(i.indicator, idx) for idx, i in enumerate(indicators) if i.itype == 'url']

        predict = predict_url([u[0] for u in urls])

        for idx, u in enumerate(urls):
            indicators[u[1]].probability = round((predict[idx][0] * 100), 2)

        return indicators

    def predict_fqdns(self, indicators):
        indicators = list(indicators)
        urls = [(i.indicator, idx) for idx, i in enumerate(indicators) if i.itype == 'fqdn']

        predict = predict_fqdn([u[0] for u in urls])

        for idx, u in enumerate(urls):
            indicators[u[1]].probability = round((predict[idx][0] * 100), 2)

        return indicators

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

        if rule.feeds[feed].get('limit') and limit == 25:
            limit = rule.feeds[feed].get('limit')

        if parser_name != 'csirtg':
            # detect and load the parser
            plugin_path = os.path.join(os.path.dirname(__file__), 'parsers')
            parser = load_plugin(plugin_path, parser_name)
            parser = parser.Plugin(rule=rule, feed=feed, cache=cli.cache, limit=limit)

            # bring up the pipeline
            indicators = parser.process(skip_invalid=self.skip_invalid)

        indicators = (i for i in indicators if self.is_valid(i))
        indicators = (self.clean_indicator(i) for i in indicators)

        # check to see if the indicator is too old
        if self.goback:
            indicators = (i for i in indicators if not self.is_old(i))

        if limit:
            indicators = itertools.islice(indicators, int(limit))

        # indicators = (i for i in indicators if not self.is_archived(i))
        indicators = (self.confidence(i) for i in indicators)

        if self.ml:
            indicators = self.predict_urls(indicators)
            indicators = self.predict_fqdns(indicators)

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
