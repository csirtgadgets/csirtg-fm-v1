from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

import os.path
import tempfile

VERSION = __version__


TEMP_DIR = os.path.join(tempfile.gettempdir())
RUNTIME_PATH = os.getenv('CSIRTG_SMRT_RUNTIME_PATH', TEMP_DIR)
RUNTIME_PATH = os.path.join(RUNTIME_PATH)

SMRT_CACHE = os.path.join(RUNTIME_PATH, 'smrt')
SMRT_CACHE = os.getenv('CSIRTG_SMRT_CACHE_PATH', SMRT_CACHE)
CACHE_PATH = SMRT_CACHE

SMRT_RULES_PATH = os.getenv('CSIRTG_SMRT_RULES_PATH', os.path.join(os.getcwd(), 'rules'))

# Logging stuff
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s[%(lineno)s] - %(message)s'

LOGLEVEL = 'ERROR'
LOGLEVEL = os.getenv('CSIRTG_LOGLEVEL', LOGLEVEL).upper()

FIREBALL_SIZE = os.getenv('CSIRTG_SMRT_FIREBALL_SIZE', 100)
if FIREBALL_SIZE == '':
    FIREBALL_SIZE = 100
