from csirtg_fm.parsers import Parser
import re
from pprint import pprint
import logging
from ..utils.columns import get_indicator
import os

logger = logging.getLogger(__name__)
TRACE = os.getenv('CSIRTG_FM_PARSER_TRACE', '1')

if logger.getEffectiveLevel() == logging.DEBUG:
    if TRACE == '0':
        logger.setLevel(logging.INFO)


class Delim(Parser):

    def __init__(self, **kwargs):
        super(Delim, self).__init__(**kwargs)

        if self.delim and isinstance(self.delim, str):
            self.pattern = re.compile(self.delim)

    def process(self, **kwargs):
        count = 0
        with open(self.cache, 'r', encoding='utf-8', errors='ignore') as cache:
            from ..utils.content import peek
            hints = peek(cache, lines=25, delim=self.delim)
            cache.seek(0)
            g = cache.readlines()
            if self.rule.reverse:
                g = reversed(g)

            for l in g:
                if self.ignore(l):  # comment or skip
                    continue

                l = l.rstrip()
                l = l.lstrip()

                logger.debug(l)
                m = self.pattern.split(l)

                if hasattr(self, 'strip'):
                    for idx, v in enumerate(m):
                        m[idx] = v.strip(self.strip)

                i = get_indicator(m, hints=hints)

                if not i.itype:
                    logger.error("unable to detect indicator: \n%s" % l)
                    continue

                if self.rule.defaults.get('values'):
                    for idx, v in enumerate(self.rule.defaults['values']):
                        if v:
                            setattr(i, v, m[idx])

                self.set_defaults(i)

                if self.rule.feeds[self.feed].get('values'):
                    for idx, v in enumerate(self.rule.feeds[self.feed]['values']):
                        if v:
                            setattr(i, v, m[idx])

                yield i.__dict__()

                logger.debug(i)

                count += 1
                if self.limit == count:
                    return


Plugin = Delim
