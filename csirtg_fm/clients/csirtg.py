from csirtgsdk.client import Client as CSIRTGClient
from csirtgsdk.feed import Feed
from csirtgsdk.indicator import Indicator
from pprint import pprint

class Client(object):
    def __init__(self, **kwargs):
        self.handle = CSIRTGClient()

    def ping(self):
        rv = self.handle.get('https://csirtg.io/api')
        return True

    def fetch(self, user, feed, limit=50):
        data = Feed(self.handle).show(user, feed, limit=limit)
        data = data['indicators']
        for i in data:
            i['reported_at'] = i.get('reporttime') or i.get('lasttime')
            i['last_at'] = i['lasttime']
            i['first_at'] = i.get('firsttime')
            i['provider'] = 'csirtg.io'
            i['reference'] = 'https://csirtg.io/users/%s/feeds/%s' % (user, feed)
            i['tlp'] = i.get('tlp', 'green')

        return data

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
