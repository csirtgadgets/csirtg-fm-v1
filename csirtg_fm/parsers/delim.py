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
            for l in cache.readlines():
                if self.ignore(l):  # comment or skip
                    continue

                l = l.rstrip()
                l = l.lstrip()

                logger.debug(l)
                m = self.pattern.split(l)

                i = get_indicator(m)

                if not i.itype:
                    logger.error("unable to parse line: \n%s" % l)
                    continue

                self.set_defaults(i)
                logger.debug(i)

                yield i.__dict__()


Plugin = Delim
