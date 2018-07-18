import os
from setuptools import setup, find_packages
import versioneer
import sys

import sys
if sys.version_info < (3, 5):
    sys.exit('Sorry, Python < 3,6 is not supported')

# vagrant doesn't appreciate hard-linking
if os.environ.get('USER') == 'vagrant' or os.path.isdir('/vagrant'):
    del os.link

# https://www.pydanny.com/python-dot-py-tricks.html
if sys.argv[-1] == 'test':
    test_requirements = [
        'pytest',
        'coverage',
        'pytest_cov',
    ]
    try:
        modules = map(__import__, test_requirements)
    except ImportError as e:
        err_msg = e.message.replace("No module named ", "")
        msg = "%s is not installed. Install your test requirements." % err_msg
        raise ImportError(msg)
    r = os.system('py.test -v --cov=csirtg_fm --cov-fail-under=25')
    if r == 0:
        sys.exit()
    else:
        raise RuntimeError('tests failed')

package_data = {}
if sys.platform == 'nt':
    package_data['csirtg_fm'] = os.path.join('tools', 'magic1.dll')

setup(
    name="csirtg_fm",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    package_data=package_data,
    description="The FASTEST way to consume threat intel",
    long_description="The FASTEST way to consume threat intel",
    url="https://github.com/csirtgadgets/fuzzy-chainsaw",
    license='MPL2',
    classifiers=[
               "Topic :: System :: Networking",
               "Environment :: Other Environment",
               "Intended Audience :: Developers",
               "Programming Language :: Python",
               ],
    keywords=['security'],
    author="Wes Young",
    author_email="wes@csirtgadgets.com",
    packages=find_packages(exclude=['test']),
    install_requires=[
        'csirtg_indicator>=2.0a1',
        'ipaddress',
        'feedparser',
        'requests',
        'arrow',
        'python-magic',
        'pyaml',
        'chardet',
        'lxml',
        'tzlocal',
        'SQLAlchemy',
        'tornado',
        'nltk',
        'csirtgsdk',
        'csirtg_mail',
        'csirtg-domainsml-tf',
        'csirtg-urlsml-tf',
        'csirtg-ipsml',
    ],
    entry_points={
        'console_scripts': [
            'csirtg-fm=csirtg_fm.cli:main'
        ]
    },
)
