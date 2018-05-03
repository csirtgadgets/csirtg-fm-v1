import gzip
import os.path
from zipfile import ZipFile


def decompress_gzip(f):
    with gzip.open(f, 'rb') as in_file:
        s = in_file.read()

    # Now store the uncompressed data
    path_to_store = f[:-3]  # remove the '.gz' from the filename

    # store uncompressed file data from 's' variable
    with open(path_to_store, 'w') as f:
        f.write(s)

    return path_to_store


def decompress_zip(zipfile):
    with ZipFile(zipfile) as f:
        for m in f.infolist():
            fname = os.path.join(os.path.dirname(zipfile), m.filename)
            with f.open(m.filename) as zip:
                # store uncompressed file data from 's' variable
                with open(fname, 'wb') as f:
                    f.write(zip.read())

            yield fname


# def get_lines_gzip(file):
#
#     with gzip.open(file, 'rb') as f:
#         for l in f:
#             yield l
#
#
# def get_lines_zip(file):
#     with ZipFile(file) as f:
#         for m in f.infolist():
#             with f.open(m.filename) as zip:
#                 for l in zip.readlines():
#                     yield l
