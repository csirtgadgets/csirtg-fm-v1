import os

REMOTE = os.getenv('CSIRTG_FM_SPLUNK_REMOTE')


# https://github.com/splunk/splunk-sdk-python/blob/master/examples/submit.py
class _Splunk(object):

    __name__ = 'splunk'

    def __init__(self, **kwargs):

        raise NotImplemented

    def ping(self, write=False):
        raise NotImplemented

    def indicators_create(self, data, **kwargs):
        # https://github.com/splunk/splunk-sdk-python/blob/master/examples/submit.py
        raise NotImplemented

Plugin = _Splunk
