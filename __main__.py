#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    GF.365 integration server
    ~~~~~~~
"""

__author__ = 'sangkyung.lee@gconhub.co.kr'

import signal
import time

import tornado.httpserver
import tornado.ioloop
import tornado.web
from handler import CHandler, GHandler
from tornado.options import options, define, parse_command_line

define('port', default=8890, help='default port number', type=int)
define('conf', default='./config/local.conf', help='config file', type=str)
MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = 3


def main():
    from library.logger import log, initialize

    initialize()

    # create tornado request handler
    application = tornado.web.Application([
        (r"/capi", CHandler),
        (r"/gapi", GHandler)
    ])

    # notice command signal(server shutdown)
    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    # simple multi-process(non-blocking)
    server = tornado.httpserver.HTTPServer(application)
    server.bind(options.port)
    server.start(0)
    tornado.ioloop.IOLoop.current().start()

    # exit
    log.info("Exit.")


def sig_handler(sig, frame):
    from library.logger import log

    log.warning('Caught signal: %s', sig)
    log.warning('Caught frame: %s', frame)
    tornado.ioloop.IOLoop.instance().add_callback(shutdown)


def shutdown():
    from library.logger import log

    log.info('Will shutdown in %s seconds ...', MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
    io_loop = tornado.ioloop.IOLoop.instance()

    deadline = time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN

    def stop_loop():
        now = time.time()
        if now < deadline and (io_loop._callbacks or io_loop._timeouts):
            io_loop.add_timeout(now + 1, stop_loop)
        else:
            io_loop.stop()
            log.info('shutdown.')

    stop_loop()


if __name__ == "__main__":

    parse_command_line()
    main()
    # if len(sys.argv) != 3:
    #     print('Usage 3x6game --conf=<path> --port=<port number>')
    # else:
    #     main()
