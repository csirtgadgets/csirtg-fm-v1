from csirtgsdk.client import Client as CSIRTGClient
from csirtgsdk.indicator import Indicator


class _Csirtg(object):
    def __init__(self, **kwargs):
        self.handle = CSIRTGClient()

    def ping(self):
        rv = self.handle.get('https://csirtg.io/api')
        return True

    def indicators_create(self, data):
        if not isinstance(data, list):
            data = [data]

        indicators = []
        for x in data:
            d = x.__dict__()
            d['feed'] = self.feed
            d['user'] = self.user

            i = Indicator(
                self.handle,
                d
            )

            rv = i.submit()
            indicators.append(rv)

        assert len(indicators) > 0
        return indicators
