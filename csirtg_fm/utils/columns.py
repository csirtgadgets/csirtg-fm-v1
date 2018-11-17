import socket
from csirtg_fm.utils.timestamps import parse_timestamp
from csirtg_indicator.utils import resolve_itype
from csirtg_indicator import Indicator
from pprint import pprint
import re

# py < 3.6
from collections import OrderedDict


def is_timestamp(s):
    try:
        t = parse_timestamp(s)
        return t
    except Exception:
        pass


def get_indicator(l, hints=None):
    i = OrderedDict()

    if not isinstance(l, list):
        l = [l]

    # step 1, detect datatypes
    for e in l:
        if not isinstance(e, (str, bytes)):
            continue

        e = e.rstrip()
        e = e.lstrip()

        if re.match('^[a-zA-Z]{2}$', e):
            i[e] = 'CC'
            continue

        t = None
        try:
            t = resolve_itype(e.rstrip('/'))
            # 25553.0 ASN formats trip up FQDN resolve itype
            if t and not (t == 'fqdn' and re.match('^\d+\.[0-9]$', e)):
                i[e] = 'indicator'
                continue

        except Exception:
            pass

        if isinstance(e, int):
            i[e] = 'int'
            continue

        if isinstance(e, float) or re.match('^\d+\.[0-9]$', e):
            i[e] = 'float'
            continue

        if is_timestamp(e):
            i[e] = 'timestamp'
            continue

        if isinstance(e, (str, bytes)):
            if hints:
                for ii in range(0, 25):
                    if len(hints) == ii:
                        break

                    if e.lower() == hints[ii].lower():
                        i[e] = 'description'
                        break

            if not i.get(e):
                i[e] = 'string'

    i2 = Indicator()
    timestamps = []
    ports = []

    for e in i:
        if i[e] == 'CC':
            i2.cc = e
            continue

        if i[e] == 'indicator':
            if i2.indicator:
                i2.reference = e
            else:
                i2.indicator = e
            continue

        if i[e] == 'timestamp':
            timestamps.append(parse_timestamp(e))
            continue

        if i[e] == 'float':
            i2.asn = e
            continue

        if i[e] == 'int':
            ports.append(e)
            continue

        if i[e] == 'description':
            i2.description = e
            continue

        if i[e] == 'string':
            if re.match(r'[0-9A-Za-z\.\s\/]+', e) and i2.asn:
                i2.asn_desc = e
                continue

            if 4 <= len(e) <= 10 and re.match('[a-z-A-Z]+,?', e) and e not in ['ipv4', 'fqdn', 'url', 'ipv6']:
                i2.tags = [e]
                continue

            if ' ' in e and 5 <= len(e) and not i2.asn_desc:
                i2.description = e
                continue

    timestamps = sorted(timestamps, reverse=True)

    if len(timestamps) > 0:
        i2.last_at = timestamps[0]

    if len(timestamps) > 1:
        i2.first_at = timestamps[1]

    if len(ports) > 0:
        if len(ports) == 1:
            i2.portlist = ports[0]
        else:
            if ports[0] > ports[1]:
                i2.portlist = ports[0]
                i2.dest_portlist = ports[1]
            else:
                i2.portlist = ports[1]
                i2.dest_portlist = ports[0]

    return i2


def main():
    i = ['192.168.1.1', '2015-02-28T00:00:00Z', 'scanner', '2015-02-28T01:00:00Z', 1159, 2293]
    i2 = get_indicator(i)
    print(i2)


if __name__ == "__main__":
    main()
