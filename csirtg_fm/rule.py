import yaml
import json
import logging
from csirtg_fm.exceptions import RuleUnsupported
import os

logger = logging.getLogger(__name__)


def _load_rules_dir(path):
    for f in sorted(os.listdir(path)):
        if f.startswith('.'):
            continue

        if os.path.isdir(f):
            continue

        try:
            r = Rule(path=os.path.join(path, f))
        except Exception as e:
            logger.error(e)
            yield None, None

        for feed in r.feeds:
            yield r, feed


def load_rules(rule, feed=None):
    if os.path.isdir(rule):
        for r, feed in _load_rules_dir(rule):
            yield r, feed

        return

    logger.info("processing {0}".format(rule))
    try:
        rule = Rule(path=rule)
    except Exception as e:
        logger.error(e)
        return

    if feed:
        # replace the feeds dict with the single feed
        # raises KeyError if it doesn't exist
        try:
            rule.feeds = {feed: rule.feeds[feed]}
        except Exception:
            return None

    for f in rule.feeds:
        yield rule, f


class Rule(dict):

    def __init__(self, path=None, rule=None, **kwargs):
        if path:
            if path.endswith('.yml'):
                with open(path) as f:
                    try:
                        d = yaml.load(f)
                    except Exception as e:
                        logger.error('unable to parse {0}'.format(path))
                        raise RuntimeError(e)

                self.defaults = d.get('defaults')
                self.feeds = d.get('feeds')
                self.parser = d.get('parser')
                self.fetcher = d.get('fetcher')
                self.skip = d.get('skip')
                self.skip_first = d.get('skip_first')
                self.remote = d.get('remote')
                self.provider = d.get('provider')
                self.replace = d.get('replace')
                self.itype = d.get('itype')
                self.remote_pattern = d.get('remote_pattern')
                self.token = d.get('token')
                self.token_header = d.get('token_header')
                self.username = d.get("username")
                self.password = d.get("password")
                self.filters = d.get('filters')
                self.delim_pattern = d.get('delim_pattern')
                self.line_filter = d.get('line_filter')
                self.limit = d.get('limit')
                self.reverse = d.get('reverse')

            else:
                raise RuleUnsupported('unsupported file type: {}'.format(path))
        else:
            self.defaults = rule.get('defaults')
            self.feeds = rule.get('feeds')
            self.parser = rule.get('parser')
            self.fetcher = rule.get('fetcher')
            self.skip = rule.get('skip')
            self.skip_first = rule.get('skip_first')
            self.remote = rule.get('remote')
            self.provider = rule.get('provider')
            self.replace = rule.get('replace')
            self.itype = rule.get('itype')
            self.remote_pattern = rule.get('remote_pattern')
            self.token = rule.get('token')
            self.token_header = rule.get('token_header')
            self.username = rule.get('username')
            self.password = rule.get('password')
            self.filters = rule.get('filters')
            self.delim_pattern = rule.get('delim_pattern')
            self.line_filter = rule.get('line_filter')
            self.limit = rule.get('limit')
            self.reverse = rule.get('reverse')

        if self.token and self.token.endswith('_TOKEN'):
            self.token = os.getenv(self.token)

    def __repr__(self):
        return json.dumps({
            "defaults": self.defaults,
            "feeds": self.feeds,
            "parser": self.parser,
            "fetcher": self.fetcher,
            'skip': self.skip,
            "skip_first": self.skip_first,
            'remote': self.remote,
            'remote_pattern': self.remote_pattern,
            'replace': self.replace,
            'itype': self.itype,
            'filters': self.filters,
            'delim_pattern': self.delim_pattern,
            'line_filter': self.line_filter,
            'limit': self.limit,
            'token': self.token,
            'reverse': self.reverse
        }, sort_keys=True, indent=4, separators=(',', ': '))