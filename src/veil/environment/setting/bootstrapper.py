from __future__ import unicode_literals, print_function, division
import logging
import sys
import os.path
from .option import register_option
from veil.environment import *

LOGGER = logging.getLogger(__name__)
boostrapped = False

get_logging_level = register_option('logging', 'level', default='DEBUG')

def bootstrap_runtime():
    global boostrapped
    if boostrapped:
        return
    else:
        boostrapped = True

    __dir__ = os.path.dirname(__file__)
    if __dir__ in sys.path:
        sys.path.remove(__dir__) # disable old style relative import
    handler = logging.StreamHandler(os.fdopen(sys.stderr.fileno(), 'w', 0))
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    def configure_logging():
        LOGGING_LEVEL_VALUES = {}
        for level in [logging.DEBUG, logging.INFO, logging.WARN, logging.ERROR, logging.CRITICAL]:
            LOGGING_LEVEL_VALUES[logging.getLevelName(level)] = level
        level = LOGGING_LEVEL_VALUES[get_logging_level() or 'INFO']
        loggers = ['veil']
        loggers.extend([c.__name__ for c in get_application_components()])
        for logger in loggers:
            logger = logging.getLogger(logger)
            logger.setLevel(level)
            logger.addHandler(handler)

    configure_logging()


def logging_settings(logging_level):
    return {'veil': {'logging': {'level': logging_level}}}