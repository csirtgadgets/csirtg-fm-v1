import logging
import logging.handlers


class _Syslog(object):

    __name__ = 'syslog'

    def __init__(self, remote='localhost:514', **kwargs):
        self.remote = remote

        self.port = 514
        if ':' in self.remote:
            self.remote, self.port = self.remote.split(':')

        self.port = int(self.port)

        self.logger = logging.getLogger('csirtg-smrt')
        self.logger.setLevel(logging.INFO)
        handler = logging.handlers.SysLogHandler(address=(self.remote, self.port))
        self.logger.addHandler(handler)

    def indicators_create(self, data, **kwargs):
        if not isinstance(data, list):
            data = [data]

        for i in data:
            first_at = i.first_at
            if first_at:
                first_at = first_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            last_at = i.last_at
            if last_at:
                last_at = last_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            reported_at = i.reported_at
            if reported_at:
                reported_at = reported_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            line = "provider={} indicator={} tlp={} first_at={} last_at={} reported_at={}".format(
                i.provider,
                i.indicator,
                i.tlp,
                first_at,
                last_at,
                reported_at,
            )
            self.logger.info(line)


Plugin = _Syslog
