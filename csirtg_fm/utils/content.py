import magic
import sys
from pprint import pprint
import re
from collections import OrderedDict

from csirtg_indicator.utils import resolve_itype

RE_SUPPORTED_DECODE = re.compile("zip|lzf|lzma|xz|lzop")

f = sys.argv[1]


def _is_ascii(f, mime):
    if mime.startswith(('text/plain', 'ASCII text')):
        return 'pattern'


def _is_flat(f, mime):
    if not _is_ascii(f, mime):
        return

    n = 5
    for l in f.readlines():
        if isinstance(l, bytes):
            l = l.decode('utf-8')

        if l.startswith('#'):
            continue

        l = l.rstrip("\n")

        try:
            resolve_itype(l)
        except:
            return False

        n -= 1
        if n == 0:
            break

    return 'csv'


def _is_xml(f, mime):
    if not mime.startswith(("application/xml", "'XML document text", 'text/xml')):
        return

    first = f.readline()
    second = f.readline().rstrip("\n")
    last = f.readlines()[-1].rstrip("\n")

    if not first.startswith("<?xml "):
        return

    if second.startswith("<rss ") and last.endswith("</rss>"):
        return 'rss'

    return 'xml'


def _is_json(f, mime):
    if mime == 'application/json':
        return 'json'

    if not _is_ascii(f, mime):
        return

    first = f.readline().rstrip("\n")
    last = first

    try:
        last = f.readlines()[-1].rstrip("\n")
    except Exception:
        pass

    if not first.startswith(("'[{", "'{")) and not first.startswith(("[{", "{")):
        return

    if not last.endswith(("}]'", "}'")) and not last.endswith(("}]", "}")):
        return

    return 'json'


def _is_delimited(f, mime):
    if not _is_ascii(f, mime):
        return

    m = OrderedDict([
        ('|', 'pipe'),
        (';', 'semicolon'),
        ("\t", 'tsv'),
        (',', 'csv'),
    ])

    first = f.readline().rstrip("\n")
    while first.startswith('#'):
        first = f.readline().rstrip("\n")

    second = f.readline().rstrip("\n")
    for d in m:
        c = first.count(d)
        if c == 0:
            continue

        # within 2
        if (c - 2) <= second.count(d) <= (c + 2):
            return m[d]

        if second.count(d) == 0 and first.count(d) > 2:
            return m[d]

    return False


def get_mimetype(f):
    try:
        ftype = magic.from_file(f, mime=True)
        return ftype
    except AttributeError:
        pass

    try:
        mag = magic.open(magic.MAGIC_MIME)
    except AttributeError as e:
        raise RuntimeError('unable to detect cached file type')

    mag.load()
    return mag.file(f)


def get_type(f_name, mime=None):
    if not mime:
        mime = get_mimetype(f_name)

    if isinstance(f_name, str):
        f = open(f_name, 'r')

    TESTS = [
        _is_xml,
        _is_json,
        _is_delimited,
        _is_flat,
        _is_ascii,
    ]

    t = None
    for tt in TESTS:
        f.seek(0)
        try:
            t = tt(f, mime)
        except:
            continue

        if t:
            return t

    if f_name.endswith('.csv') or f_name.endswith('.xls'):
        return 'csv'

    if f_name.endswith('.tsv'):
        return 'tsv'


def peek(f, lines=5, delim=','):
    n = lines
    from collections import defaultdict
    freq_dict = defaultdict(int)

    for l in f.readlines():
        if l.startswith('#'):
            continue

        for e in l.split(delim):
            if e == '':
                continue

            if e == "\n":
                continue

            if e in ['ipv4', 'ipv6', 'url', 'fqdn']:
                continue

            if re.search(r'\d+', e):
                continue

            # we don't care if it's an indicator
            from csirtg_indicator import resolve_itype
            try:
                resolve_itype(e)
            except:
                pass
            else:
                continue

            freq_dict[e] += 1

        n = n-1
        if n == 0:
            break

    return sorted(freq_dict, reverse=True)


if __name__ == "__main__":
    f = sys.argv[1]
    with open(f) as FILE:
        mime_type = magic.from_file(f)
        print(mime_type)

        print(get_type(FILE, mime_type))
