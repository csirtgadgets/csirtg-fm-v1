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

        if self.line_filter:
            self.line_filter = re.compile(self.line_filter)

        if self.rule.feeds[self.feed].get('limit'):
            self.limit = self.rule.feeds[self.feed]['limit']
        elif self.rule.limit:
            self.limit = self.rule.limit

        if self.limit is not None:
            self.limit = int(self.limit)

        self.line_count = 0

    def ignore(self, line):
        if line == '' or self.is_comment(line):
            return True

        self.line_count += 1
        if self.line_count == 1 and self.skip_first:
            return True

        if self.skip and self.skip.search(line):
            return True

        if self.line_filter and not self.line_filter.search(line):
            return True

    def is_comment(self, line):
        if self.comments.search(line):
            return True

    def _defaults(self):
        defaults = self.rule.defaults or {}

        if not self.rule.feeds[self.feed].get('defaults'):
            return defaults

        for d in self.rule.feeds[self.feed].get('defaults'):
            if not d:
                continue

            defaults[d] = self.rule.feeds[self.feed]['defaults'][d]

        return defaults

    def set_defaults(self, i):
        if not self.rule.defaults and not self.rule.feeds[self.feed].get('defaults'):
            return

        for k, v in self._defaults().items():
            if isinstance(v, str) and ',' in v:
                v = v.replace(' ', '')
                v = v.split(',')
            setattr(i, k, v)

        if not i.reference or i.reference == '':
            i.reference = self.rule.feeds[self.feed].get('remote')

    def process(self):
        raise NotImplementedError
