#!/usr/bin/env python3

import logging
import os.path
import textwrap
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from pprint import pprint
import sys
import select
import arrow
from time import sleep
import tornado.ioloop as ioloop
from random import randint
from multiprocessing import Process

from csirtg_indicator.format import FORMATS
from csirtg_indicator.constants import COLUMNS

from csirtg_fm.constants import FM_RULES_PATH, CACHE_PATH
from csirtg_fm.utils import setup_logging, get_argument_parser, setup_signals
from csirtg_fm.utils.content import get_type
from csirtg_fm import FM
from .rule import load_rules
from .archiver import Archiver, NOOPArchiver

FORMAT = os.getenv('CSIRTG_FM_FORMAT', 'table')
STDOUT_FIELDS = COLUMNS
ARCHIVE_PATH = os.environ.get('CSIRTG_SMRT_ARCHIVE_PATH', CACHE_PATH)
ARCHIVE_PATH = os.path.join(ARCHIVE_PATH, 'fm.db')
GOBACK_DAYS = 3
SERVICE_INTERVAL = os.getenv('CSIRTG_FM_SERVICE_INTERVAL', 60)
LIMIT = os.getenv('CSIRTG_FM_LIMIT', 25)
LIMIT = int(LIMIT)

logger = logging.getLogger(__name__)

logging.getLogger('asyncio').setLevel(logging.WARNING)


def _run_fm(args, **kwargs):
    data = kwargs.get('data')

    verify_ssl = True
    if args.no_verify_ssl:
        verify_ssl = False

    archiver = NOOPArchiver()
    if args.remember:
        archiver = Archiver(dbfile=args.remember_path)

    goback = args.goback
    if goback:
        goback = arrow.utcnow().replace(days=-int(goback))

    logger.info('starting run...')

    s = FM(archiver=archiver, client=args.client, goback=goback, ml=args.ml)

    fetch = True
    if args.no_fetch:
        fetch = False

    data = []
    indicators = []

    for r, f in load_rules(args.rule, feed=args.feed):
        if not f:
            print("\n")
            print('Feed not found: %s' % args.feed)
            print("\n")
            raise SystemExit

        # detect which client we should be using

        if '/' in f:
            parser_name = 'csirtg'
            cli = None
            if not os.getenv('CSIRTG_TOKEN'):
                logger.info('')
                logger.info('CSIRTG_TOKEN var not set in ENV, skipping %s' % f)
                logger.info('Sign up for a Free account: https://csirtg.io')
                logger.info('')
                continue

            for i in s.fetch_csirtg(f, limit=args.limit):
                data.append(i)

        else:
            from .clients.http import Client
            cli = Client(r, f, verify_ssl=verify_ssl)

            # fetch the feeds
            cli.fetch(fetch=fetch)

            # decode the content and load the parser
            try:
                logger.debug('testing parser: %s' % cli.cache)
                parser_name = get_type(cli.cache)
                logger.debug('detected parser: %s' % parser_name)
            except Exception as e:
                logger.debug(e)

            if r.feeds[f].get('pattern'):
                parser_name = 'pattern'

            if not parser_name:
                parser_name = r.feeds[f].get('parser') or r.parser or 'pattern'

                # process the indicators by passing the parser and file handle [or data]
                logger.info('processing: {} - {}:{}'.format(args.rule, r.provider, f))

        try:
            for i in s.process(r, f, parser_name, cli, limit=args.limit, indicators=data):
                if not i:
                    continue

                indicators.append(i)

        except Exception as e:
            logger.error(e)
            import traceback
            traceback.print_exc()

    if args.client == 'stdout':
        for l in FORMATS[args.format](data=indicators, cols=args.fields.split(',')):
            print(l)

    logger.info('cleaning up')
    archiver.cleanup()
    archiver.clear_memcache()

    logger.info('finished run')
    if args.service:
        logger.info('sleeping...')


def main():
    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
        Env Variables:
            CSIRTG_RUNTIME_PATH


        example usage:
            $ csirtg-fm -r rules/default
            $ csirtg-fm -r csirtg.yml --feed csirtgadgets/darknet
            $ CIF_TOKEN=1234 csirtg-fm -r csirtg.yml --client cif -d
        '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='csirtg-fm',
        parents=[p],
    )

    p.add_argument("-r", "--rule", help="specify the rules directory or specific rules file [default: %(default)s",
                   default=FM_RULES_PATH)

    p.add_argument("-f", "--feed", help="specify the feed to process")

    p.add_argument("--limit", help="limit the number of records processed [default: %(default)s]",
                   default=25)

    p.add_argument('--no-fetch', help='do not re-fetch if the cache exists', action='store_true')
    p.add_argument('--no-verify-ssl', help='turn TLS/SSL verification OFF', action='store_true')

    p.add_argument('--skip-invalid', help="skip invalid indicators in DEBUG (-d) mode", action="store_true")
    p.add_argument('--skip-broken', help='skip seemingly broken feeds', action='store_true')

    p.add_argument('--format', help='specify output format [default: %(default)s]"', default=FORMAT,
                   choices=FORMATS)
    p.add_argument('--fields', help='specify fields for stdout [default %(default)s]"', default=','.join(STDOUT_FIELDS))

    p.add_argument('--remember-path', help='specify remember db path [default: %(default)s', default=ARCHIVE_PATH)
    p.add_argument('--remember', help='remember what has been already processed', action='store_true')

    p.add_argument('--client', default='stdout')

    p.add_argument('--goback', help='specify default number of days to start out at [default %(default)s]',
                   default=GOBACK_DAYS)

    p.add_argument('--service', action='store_true', help="start in service mode")
    p.add_argument('--service-interval', help='set run interval [in minutes, default %(default)s]',
                   default=SERVICE_INTERVAL)
    p.add_argument('--delay', help='specify initial delay', default=randint(5, 55))

    p.add_argument('--ml', action='store_true')

    args = p.parse_args()

    setup_logging(args)

    if not args.service:
        data = None
        if select.select([sys.stdin, ], [], [], 0.0)[0]:
            data = sys.stdin.read()
        try:
            _run_fm(**{
                'args': args,
                'data': data,
            })
        except KeyboardInterrupt:
            logger.info('exiting..')

        raise SystemExit

    # we're running as a service
    setup_signals(__name__)
    service_interval = int(args.service_interval)
    r = float(args.delay)

    if r > 0:
        logger.info("random delay is {}, then running every {} min after that".format(r, service_interval))
        try:
            sleep((r * 60))

        except KeyboardInterrupt:
            logger.info('shutting down')
            raise SystemExit

        except Exception as e:
            logger.error(e)
            raise SystemExit

    # we run the service as a fork, a cleaner way to give back any memory consumed by large feed processing
    def _run_fork():
        logger.debug('forking process...')
        p = Process(target=_run_fm, args=(args,))
        p.daemon = False
        p.start()
        p.join()

    # first run, PeriodicCallback has builtin wait..
    _run_fork()

    main_loop = ioloop.IOLoop()
    service_interval = (service_interval * 60000)
    loop = ioloop.PeriodicCallback(_run_fork, service_interval)

    try:
        loop.start()
        main_loop.start()

    except KeyboardInterrupt:
        logger.info('exiting..')
        pass

    except Exception as e:
        logger.error(e)
        pass


if __name__ == "__main__":
    main()
