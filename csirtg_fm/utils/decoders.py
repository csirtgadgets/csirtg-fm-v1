import gzip
import os.path
from zipfile import ZipFile


def decompress_gzip(f):
    with gzip.open(f, 'rb') as in_file:
        s = in_file.read()

    # Now store the uncompressed data
    path_to_store = f[:-3]  # remove the '.gz' from the filename

    try:
        os.remove(path_to_store)
    except:
        pass

    # store uncompressed file data from 's' variable
    with open(path_to_store, 'wb') as f:
        f.write(s)

    return path_to_store


def decompress_zip(zipfile):
    with ZipFile(zipfile) as f:
        for m in f.infolist():
            fname = os.path.join(os.path.dirname(zipfile), m.filename)
            try:
                os.remove(fname)
            except:
                pass

            with f.open(m.filename) as zip:
                # store uncompressed file data from 's' variable
                with open(fname, 'wb') as f:
                    f.write(zip.read())

            yield fname
