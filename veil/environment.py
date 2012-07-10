from __future__ import unicode_literals, print_function, division
from os import getenv
from ConfigParser import RawConfigParser
import sys
import os
from logging import DEBUG, INFO, WARN, ERROR, CRITICAL, getLogger, StreamHandler, Formatter
from logging import getLevelName
from sandal.smart_path import SmartPath
from sandal.option import register_option
from sandal.event import subscribe_event
from sandal.const import consts

__all__ = ['VEIL_HOME']

VEIL_HOME = getenv('VEIL_HOME')
assert VEIL_HOME, 'must specify $VEIL_HOME'
VEIL_HOME = SmartPath(VEIL_HOME)

get_logging_level = register_option('logging', 'level')

handler = StreamHandler(os.fdopen(sys.stderr.fileno(), 'w', 0))
handler.setFormatter(Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

def configure_logging():
    LOGGING_LEVEL_VALUES = {}
    for level in [DEBUG, INFO, WARN, ERROR, CRITICAL]:
        LOGGING_LEVEL_VALUES[getLevelName(level)] = level
    level = LOGGING_LEVEL_VALUES[get_logging_level() or 'DEBUG']
    logger = getLogger('veil')
    logger.setLevel(level)
    logger.addHandler(handler)

subscribe_event(consts.EVENT_OPTIONS_INITIALIZED, configure_logging)
