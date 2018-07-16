from csirtg_fm.parsers import Parser
import re
from pprint import pprint
import logging
from ..utils.columns import get_indicator

logger = logging.getLogger(__name__)


class Delim(Parser):

    def __init__(self, **kwargs):
        super(Delim, self).__init__(**kwargs)

        if self.delim and isinstance(self.delim, str):
            self.pattern = re.compile(self.delim)

    def process(self):
        count = 0
        with open(self.cache, 'r') as cache:
            from ..utils.content import peek
            hints = peek(cache, lines=25, delim=self.delim)
            cache.seek(0)
            for l in cache.readlines():
                if self.ignore(l):  # comment or skip
                    continue

                l = l.rstrip()
                l = l.lstrip()

                logger.debug(l)
                m = self.pattern.split(l)

                i = get_indicator(m, hints=hints)

                if not i.itype:
                    logger.error("unable to parse line: \n%s" % l)
                    continue

                if self.rule.defaults.get('values'):
                    for idx, v in enumerate(self.rule.defaults['values']):
                        if not getattr(i, v):
                            setattr(i, v, m[idx])

                self.set_defaults(i)

                if self.rule.feeds[self.feed].get('values'):
                    for idx, v in enumerate(self.rule.feeds[self.feed]['values']):
                        if not getattr(i, v):
                            setattr(i, v, m[idx])

                yield i.__dict__()

                logger.debug(i)

                count += 1
                if self.limit and int(self.limit) == count:
                    return


Plugin = Delim
