from __future__ import unicode_literals, print_function, division
import datetime
import logging
import os
import sys
import json
import time
import socket
import traceback
from .component_map import get_root_component

VEIL_LOGGING_LEVEL_CONFIG = 'VEIL_LOGGING_LEVEL_CONFIG'
VEIL_LOGGING_EVENT = 'VEIL_LOGGING_EVENT'
logging_levels = None
configured_root_loggers = set()
log_context_providers = []

def add_log_context_provider(provider):
    log_context_providers.append(provider)

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
    logging_level = get_logging_level(component_name)
    logger.setLevel(logging_level)
    root_component_name = get_root_component(component_name)
    configure_root_component_logger(root_component_name or component_name)


def get_logging_level(target):
    matched_component_names = []
    for component_name in logging_levels.keys():
        if target == component_name or target.startswith('{}.'.format(component_name)):
            matched_component_names.append(component_name)
    if not matched_component_names:
        return logging_levels.get('__default__', logging.DEBUG)
    return logging_levels[max(matched_component_names)]


def configure_root_component_logger(component_name):
    if component_name in configured_root_loggers:
        return
    configured_root_loggers.add(component_name)

    logger = logging.getLogger(component_name)
    human_handler = logging.StreamHandler(os.fdopen(sys.stdout.fileno(), 'w', 0))
    human_handler.setFormatter(ColoredFormatter(
        fmt='%(asctime)s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'))
    logger.addHandler(human_handler)
    if os.getenv('VEIL_LOGGING_EVENT'):
        machine_handler = logging.StreamHandler(os.fdopen(sys.stderr.fileno(), 'w', 0))
        machine_handler.setFormatter(EventFormatter())
        logger.addHandler(machine_handler)


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        record.msg = to_unicode(record.msg)
        if record.levelno >= logging.WARNING:
            return COLOR_WRAPPERS['RED'](super(ColoredFormatter, self).format(record))
        if record.args and isinstance(record.args, dict):
        #            record.args = {k: to_str(v) for k, v in record.args.items()}
            if record.args.get('__color__'):
                wrap = COLOR_WRAPPERS.get(record.args['__color__'])
                return wrap(super(ColoredFormatter, self).format(record))
        return super(ColoredFormatter, self).format(record)


class EventFormatter(logging.Formatter):
    def format(self, record):
        record.msg = to_unicode(record.msg)
        event_name = record.message.split(':')[0]
        event = {
            '@type': 'veil',
            '@source': socket.gethostname(),
            '@message': record.getMessage(),
            '@timestamp': time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            '@fields': {
                'logged_by': record.name,
                'level': record.levelname,
                'event': event_name
            }
        }
        if record.args and isinstance(record.args, dict):
            event['@fields'].update(dump_dict(record.args))
        if record.exc_info:
            event['@fields']['exception_type'] = unicode(record.exc_info[0])
            event['@fields']['exception_stack_trace'] = self.formatException(record.exc_info)
        event['@fields'].update(get_log_context())
        return json.dumps(event)


def get_log_context():
    context = {}
    for provider in log_context_providers:
        try:
            context.update(provider())
        except:
            traceback.print_exc()
    return context

def dump_dict(args):
    def format_value(v):
        if isinstance(v, basestring):
            return to_unicode(v)
        if isinstance(v, (datetime.datetime, datetime.date, datetime.time)):
            return v.isoformat()
        return unicode(v)

    return {unicode(k): format_value(v) for k, v in args.items()}


def to_unicode(s):
    if isinstance(s, unicode):
        return s
    if isinstance(s, (str, bytes)):
        try:
            return unicode(s, encoding='utf-8')
        except UnicodeDecodeError:
            return unicode(s, encoding='gb18030')
    return unicode(s)
