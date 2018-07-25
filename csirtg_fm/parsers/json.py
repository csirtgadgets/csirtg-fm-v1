import copy
import json
from csirtg_fm.parsers import Parser
import logging
import os
from pprint import pprint
from csirtg_fm.utils.columns import get_indicator

TRACE = os.environ.get('CSIRTG_FM_PARSER_TRACE')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not TRACE:
    logger.setLevel(logging.ERROR)


class Json(Parser):

    def __init__(self, *args, **kwargs):
        super(Json, self).__init__(*args, **kwargs)

    def process(self, **kwargs):
        map = self.rule.feeds[self.feed].get('map')
        values = self.rule.feeds[self.feed].get('values')
        envelope = self.rule.feeds[self.feed].get('envelope')

        count = 0
        with open(self.cache, 'rb') as cache:
            for l in cache.readlines():
                l = l.decode('utf-8')

                try:
                    l = json.loads(l)
                except ValueError as e:
                    logger.error('json parsing error: {}'.format(e))
                    continue

                if envelope:
                    l = l[envelope]

                for e in l:
                    m = [e[ii] for ii in e]
                    i = get_indicator(m)
                    self.set_defaults(i)

                    if map:
                        for x, c in enumerate(map):
                            #i[values[x]] = e[c]
                            setattr(i, values[x], e[c])

                    logger.debug(i)

                    yield i.__dict__()

                    count += 1

                    if self.limit and int(self.limit) == count:
                        return


Plugin = Json
