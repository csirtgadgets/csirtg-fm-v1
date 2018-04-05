from csirtg_indicator import Indicator
import abc


class Client(object):

    def __init__(self, **kwargs):
        pass

    def _kv_to_indicator(self, kv):
        return Indicator(**kv)

    def ping(self, write=False):
        return True

    def start(self):
        return True

    def stop(self):
        return True

    @abc.abstractmethod
    def indicators_create(self, data, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def indicators_search(self, data, **kwargs):
        raise NotImplementedError
