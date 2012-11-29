from __future__ import unicode_literals, print_function, division
import logging
import os
import sys
import json
import time
from .component_map import get_root_component

VEIL_LOGGING_LEVEL_CONFIG = 'VEIL_LOGGING_LEVEL_CONFIG'
VEIL_LOGGING_EVENT = 'VEIL_LOGGING_EVENT'
logging_levels = None
configured_root_loggers = set()

def wrap_console_text_with_color(code):
    def inner(text, bold=False):
        c = code
        if bold:
            c = "1;%s" % c
        return "\033[%sm%s\033[0m" % (c, text)

    return inner

COLOR_WRAPPERS = {
    'RED': wrap_console_text_with_color('31'),
    'GREEN': wrap_console_text_with_color('32')
}

def configure_logging(component_name):
    load_logging_levels()
    configure_component_logger(component_name)


def load_logging_levels():
    global logging_levels
    if logging_levels is not None:
        return
    logging_levels = {}
    veil_logging_level_config = os.getenv(VEIL_LOGGING_LEVEL_CONFIG)
    if not veil_logging_level_config:
        return
    with open(veil_logging_level_config) as f:
        lines = f.readlines()
    for line in lines:
        logger_name, logging_level = line.split('=')
        logging_level = getattr(logging, logging_level.strip())
        logging_levels[logger_name] = logging_level


def configure_component_logger(component_name):
    logger = logging.getLogger(component_name)
    logger.setLevel(logging_levels.get(component_name, logging.DEBUG))
    root_component_name = get_root_component(component_name)
    configure_root_component_logger(root_component_name or component_name)


def configure_root_component_logger(component_name):
    if component_name in configured_root_loggers:
        return
    configured_root_loggers.add(component_name)

    logger = logging.getLogger(component_name)
    human_handler = logging.StreamHandler(os.fdopen(sys.stdout.fileno(), 'w', 0))
    human_handler.setFormatter(ColoredFormatter(
        fmt='%(asctime)s [%(name)s] %(message)s',
        datefmt='%H:%M:%S'))
    logger.addHandler(human_handler)
    if os.getenv('VEIL_LOGGING_EVENT'):
        machine_handler = logging.StreamHandler(os.fdopen(sys.stderr.fileno(), 'w', 0))
        machine_handler.setFormatter(EventFormatter())
        logger.addHandler(machine_handler)


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno >= logging.WARNING:
            return COLOR_WRAPPERS['RED'](super(ColoredFormatter, self).format(record))
        if record.args and isinstance(record.args, dict):
            if record.args.get('__color__'):
                wrap = COLOR_WRAPPERS.get(record.args['__color__'])
                return wrap(super(ColoredFormatter, self).format(record))
        return super(ColoredFormatter, self).format(record)


class EventFormatter(logging.Formatter):
    def format(self, record):
        event_name = record.message.split(':')[0]
        event = {
            '@type': '{}/{}'.format(record.name, event_name),
            '@tags': [record.levelname],
            '@message': record.getMessage(),
            '@timestamp': time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
        }
        if record.args and isinstance(record.args, dict):
            event['@fields'] = dict(record.args)
        if record.exc_info:
            event['@fields']['exception_type'] = unicode(record.exc_info[0])
            event['@fields']['exception_stack_trace'] = self.formatException(record.exc_info)
        return json.dumps(event)