from csirtgsdk.client import Client as CSIRTGClient
from csirtgsdk.indicator import Indicator
import csirtg_indicator
from csirtg_fm.client.plugin import Client
from pprint import pprint
import os


class _Csirtg(Client):

    def __init__(self, **kwargs):
        super(_Csirtg, self).__init__(**kwargs)

    def indicators_search(self, filters):
        handle = CSIRTGClient()
        return []

    def indicators_create(self, data):
        handle = CSIRTGClient()

        if not isinstance(data, list):
            data = [data]

        indicators = []
        for x in data:
            d = {}

            if isinstance(x, csirtg_indicator.Indicator):
                d = x.__dict__()
            else:
                d = x

            d['feed'] = self.feed
            d['user'] = self.user

            i = Indicator(
                handle,
                d
            )

            rv = i.submit()
            indicators.append(rv)

        assert len(indicators) > 0
        return indicators


Plugin = _Csirtg
