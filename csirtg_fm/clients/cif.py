from cifsdk.client.http import HTTP as HTTPClient


class CIF(HTTPClient):

    def __init__(self, **kwargs):
        super(CIF, self).__init__(**kwargs)
        self.nowait = True

    def ping(self):
        return self.ping_write()


Plugin = CIF
