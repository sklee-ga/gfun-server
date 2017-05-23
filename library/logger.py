# -*- coding: utf-8 -*-
"""
    logging
    ~~~~~~~

    Implements the logging support for GameServer.
"""

import sys
import logging
import logging.config
import logging.handlers


__all__ = ['log']

log = logging.getLogger('root')


def initialize():

    LOGGING = {
        'version': 1,
        'formatters': {
            'detail': {
                'class': 'logging.Formatter',
                'format': '%(asctime)s, %(levelname)s - %(name)s - [%(filename)s:%(lineno)d], %(message)s'
            },
            'simple': {
                'format': '%(levelname)s %(name)s [%(filename)s:%(lineno)d], %(message)s'
            },
        },
        'loggers': {
            'root': {
                'handlers': ['file', 'console'],
                'level': 'DEBUG',
            },
            'tornado': {
                'handlers': ['file'],
                'level': 'INFO',
            },
        },
        'handlers': {
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'detail',
                'filename': '/tmp/gfun-gameserver.log',
                'maxBytes': 1024 * 1024 * 1,
                'backupCount': 5,
                'encoding': 'utf-8',
            },
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
                'stream': sys.stdout,
            }
        }
    }

    logger_root = logging.getLogger('root')
    logging.config.dictConfig(LOGGING)

    # logging messages are not passed to the handlers of ancestor loggers.
    logger_root.propagate = False

    # set colour
    # green
    logging.addLevelName(logging.DEBUG, "\033[32m%s\033[0m" % logging.getLevelName(logging.DEBUG))
    # YELLOW
    logging.addLevelName(logging.WARNING, "\033[33m%s\033[0m" % logging.getLevelName(logging.WARNING))
    # PURPLE
    logging.addLevelName(logging.ERROR, "\033[35m%s\033[0m" % logging.getLevelName(logging.ERROR))
    # RED
    logging.addLevelName(logging.CRITICAL, "\033[31m%s\033[0m" % logging.getLevelName(logging.CRITICAL))

    # logger_root.info('Logger initialized......')



