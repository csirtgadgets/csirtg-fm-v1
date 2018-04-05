import logging
import subprocess
import os
from pprint import pprint
from csirtg_fm.constants import VERSION, FM_CACHE
from datetime import datetime
import magic
import re
import sys
from time import sleep
import arrow
import requests


RE_SUPPORTED_DECODE = re.compile("zip|lzf|lzma|xz|lzop")
RE_CACHE_TYPES = re.compile('([\w.-]+\.(csv|zip|txt|gz))$')

FETCHER_TIMEOUT = os.getenv('CSIRTG_FM_FETCHER_TIMEOUT', 120)
RETRIES = os.getenv('CSIRTG_FM_FETCHER_RETRIES', 3)
RETRIES_DELAY = os.getenv('CSIRTG_FM_FETCHER_RETRY_DELAY', 30)  # seconds
NO_HEAD = os.getenv('CSIRTG_FM_FETCHER_NOHEAD')

logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)


class Client(object):

    def __init__(self, rule, feed, **kwargs):
        pass

    def _process_data(self, split="\n", rstrip=True):
        if isinstance(self.data, list):
            for d in self.data:
                yield d

            return

        if not split:
            yield self.data
            return

        for l in self.data.split(split):
            if rstrip:
                l = l.rstrip()

            yield l

    def _process_cache(self, split="\n", rstrip=True):
        try:
            ftype = magic.from_file(self.cache, mime=True)
        except AttributeError:
            try:
                mag = magic.open(magic.MAGIC_MIME)
                mag.load()
                ftype = mag.file(self.cache)
            except AttributeError as e:
                raise RuntimeError('unable to detect cached file type')

        if ftype.startswith('application/x-gzip') or ftype.startswith('application/gzip'):
            from csirtg_fm.decoders.zgzip import get_lines
            for l in get_lines(self.cache, split=split):
                yield l

            return

        if ftype == "application/zip":
            from csirtg_fm.decoders.zzip import get_lines
            for l in get_lines(self.cache, split=split):
                yield l

            return

        # all others, mostly txt, etc...
        with open(self.cache) as f:
            for l in f:
                yield l

    def process(self, split="\n", rstrip=True):

        if self.no_fetch and os.path.isfile(self.cache):
            logger.info('skipping fetch: {}'.format(self.cache))
        else:
            try:
                self._fetch()
            except Exception as e:
                logger.error(e)

        for l in self._process_cache(split=split, rstrip=rstrip):
            if rstrip:
                l = l.rstrip()

            if isinstance(l, bytes):
                try:
                    l = l.decode('utf-8')
                except Exception:
                    try:
                        l = l.decode('latin-1')
                    except Exception:
                        logger.error('unable to decode %s' % l)
                        continue

            yield l

        return
