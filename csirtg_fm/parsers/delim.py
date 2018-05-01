from csirtg_fm.parsers import Parser
import re
from pprint import pprint
import logging
from ..utils.columns import get_indicator

logger = logging.getLogger(__name__)


class Delim(Parser):

    def __init__(self, **kwargs):
        super(Delim, self).__init__(**kwargs)

        if self.pattern and isinstance(self.pattern, str):
            self.pattern = re.compile(self.pattern)

    def process(self):
        with open(self.cache, 'r') as cache:
            from ..utils.content import peek
            hints = peek(cache)
            pprint(hints)
            cache.seek(0)
            for l in cache.readlines():
                if self.ignore(l):  # comment or skip
                    continue

                l = l.rstrip()
                l = l.lstrip()

                m = self.pattern.split(l)

                i = get_indicator(m, hints=hints)

                if not i.itype:
                    logger.error("unable to parse line: \n%s" % l)
                    continue

                self.set_defaults(i)

                yield i.__dict__()


Plugin = Delim
