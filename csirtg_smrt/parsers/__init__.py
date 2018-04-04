import logging
import re
import math
from ..constants import FIREBALL_SIZE
import logging

RE_COMMENTS = '^([#|;]+)'

logger = logging.getLogger(__name__)

class Parser(object):

    def __init__(self, **kwargs):

        self.cache = kwargs.get('cache')
        self.rule = kwargs.get('rule')
        self.feed = kwargs.get('feed')
        self.skip_first = kwargs.get('skip_first')
        self.skip = kwargs.get('skip')
        self.line_filter = kwargs.get('line_filter')
        self.limit = kwargs.get('limit')

        # if fireball:
        #     self.fireball = int(FIREBALL_SIZE)
        # else:
        #     self.fireball = False
        #
        # if self.limit is not None:
        #     self.limit = int(limit)

        self.comments = re.compile(RE_COMMENTS)

        if self.rule.feeds[self.feed].get('skip'):
            self.skip = re.compile(self.rule.feeds[self.feed]['skip'])
        elif self.rule.skip:
            self.skip = re.compile(self.rule.skip)

        if self.rule.feeds[self.feed].get('skip_first'):
            self.skip_first = True
        elif self.rule.skip_first:
            self.skip_first = True

        if self.rule.feeds[self.feed].get('itype'):
            self.itype = self.rule.feeds[self.feed]['itype']
        elif self.rule.itype:
            self.itype = self.rule.itype

        if self.rule.feeds[self.feed].get('line_filter'):
            self.line_filter = self.rule.feeds[self.feed]['line_filter']
        elif self.rule.line_filter:
            self.line_filter = self.rule.line_filter

        # if self.line_filter:
        #     self.line_filter = re.compile(self.line_filter)

        self.line_count = 0

    def ignore(self, line):
        if line == '':
            return True

        if self.is_comment(line):
            return True

        self.line_count += 1
        if self.line_count == 1 and self.skip_first:
            return True

        if self.skip:
            if self.skip.search(line):
                return True

        if self.line_filter:
            if not self.line_filter.search(line):
                return True

    def is_comment(self, line):
        if self.comments.search(line):
            return True

    def _defaults(self):
        defaults = self.rule.defaults

        if self.rule.feeds[self.feed].get('defaults'):
            for d in self.rule.feeds[self.feed].get('defaults'):
                defaults[d] = self.rule.feeds[self.feed]['defaults'][d]

        return defaults

    def set_defaults(self, i):
        for k, v in self._defaults().items():
            setattr(i, k, v)

    def process(self):
        raise NotImplementedError
