import re
import logging
import os

from csirtg_fm.parsers import Parser
from csirtg_fm.utils.columns import get_indicator

TRACE = os.getenv('CSIRTG_FM_PARSER_TRACE', '1')

logger = logging.getLogger(__name__)

# turn on verbose debugging if _TRACE is the default
if logger.getEffectiveLevel() == logging.DEBUG:
    if TRACE == '0':
        logger.setLevel(logging.INFO)


class Pattern(Parser):

    def __init__(self, *args, **kwargs):
        super(Pattern, self).__init__(*args, **kwargs)

        self.pattern = self.rule.defaults.get('pattern', '^\S+$')

        if self.rule.feeds[self.feed].get('pattern'):
            self.pattern = self.rule.feeds[self.feed].get('pattern')

        if self.pattern:
            self.pattern = re.compile(self.pattern)

        self.split = "\n"

        if self.rule.feeds[self.feed].get('values'):
            self.cols = self.rule.feeds[self.feed].get('values')
        else:
            self.cols = self.rule.defaults.get('values', [])

        self.defaults = self._defaults()

        if isinstance(self.cols, str):
            self.cols = self.cols.split(',')

    def process(self, **kwargs):
        count = 0
        with open(self.cache, 'r', encoding='utf-8', errors='ignore') as cache:
            for l in cache.readlines():
                if self.ignore(l):  # comment or skip
                    continue

                l = l.rstrip()
                l = l.replace('\"', '')

                logger.debug(l)
                try:
                    m = self.pattern.search(l).groups()
                except ValueError as e:
                    continue
                except AttributeError as e:
                    continue

                # prob a single feed file
                if len(m) == 0:
                    m = [l]

                i = get_indicator(m)

                self.set_defaults(i)

                if self.cols:
                    for idx, col in enumerate(self.cols):
                        try:
                            setattr(i, col, m[idx])
                        except Exception as e:
                            if kwargs.get('skip_invalid', False):
                                continue
                            raise

                logger.debug(i)

                if not i.itype:
                    logger.error("unable to parse line: \n%s" % l)
                    continue

                yield i.__dict__()

                count += 1

                if self.limit and int(self.limit) == count:
                    return


Plugin = Pattern
