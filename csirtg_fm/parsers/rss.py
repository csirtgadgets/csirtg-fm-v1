import copy
import re
import logging
import feedparser
import os

from csirtg_fm.parsers import Parser
from csirtg_indicator import Indicator

logger = logging.getLogger(__name__)
TRACE = os.getenv('CSIRTG_FM_PARSER_TRACE', '1')

if logger.getEffectiveLevel() == logging.DEBUG:
    if TRACE == '0':
        logger.setLevel(logging.INFO)


class Rss(Parser):

    def __init__(self, *args, **kwargs):
        super(Rss, self).__init__(*args, **kwargs)

    def process(self, **kwargs):
        map = copy.deepcopy(self.rule.feeds[self.feed]['map'])
        for p in map:
            map[p]['pattern'] = re.compile(map[p]['pattern'])

        itype = None
        if self.rule.feeds[self.feed].get('itype'):
            itype = self.rule.feeds[self.feed].get('itype')

        feed = []
        count = 0
        with open(self.cache, 'rb') as cache:
            for l in cache.readlines():
                l = l.decode('utf-8')
                feed.append(l)

        feed = "\n".join(feed)
        try:
            feed = feedparser.parse(feed)
        except Exception as e:
            self.logger.error('Error parsing feed: {}'.format(e))
            raise e

        for e in feed.entries:
            i = Indicator()
            self.set_defaults(i)

            for k in e:
                if not map.get(k):
                    continue

                try:
                    m = map[k]['pattern'].search(e[k]).groups()
                except AttributeError:
                    continue

                for idx, c in enumerate(map[k]['values']):
                    s = m[idx]
                    if c == 'indicator' and itype == 'url' and not m[idx].startswith('http'):
                        s = 'http://%s' % s
                    setattr(i, c, s)

            logger.debug(i)

            yield i.__dict__()

            count += 1

            if self.limit and int(self.limit) == count:
                return


Plugin = Rss
