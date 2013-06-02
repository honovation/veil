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

def configure_logging(component_name):
    logger = logging.getLogger(component_name)
    logger.setLevel(get_logging_level(component_name))
    configure_root_component_logger(get_root_component(component_name) or component_name)


logging_levels = None

def load_logging_levels():
    global logging_levels
    if logging_levels is not None:
        return
    logging_levels = {}
    veil_logging_level_config = os.getenv(VEIL_LOGGING_LEVEL_CONFIG)
    if not veil_logging_level_config:
        return
    with open(veil_logging_level_config) as f:
        for line in f:
            logger_name, logging_level = [x.strip() for x in line.split('=')]
            logging_level = getattr(logging, logging_level)
            logging_levels[logger_name] = logging_level

def get_logging_level(target):
    load_logging_levels()
    matched_component_names = []
    for component_name in logging_levels.keys():
        if target == component_name or target.startswith('{}.'.format(component_name)):
            matched_component_names.append(component_name)
    if not matched_component_names:
        return logging_levels.get('__default__', logging.DEBUG)
    return logging_levels[max(matched_component_names)]


configured_root_loggers = set()

def configure_root_component_logger(root_component_name):
    if root_component_name in configured_root_loggers:
        return
    configured_root_loggers.add(root_component_name)
    logger = logging.getLogger(root_component_name)
    #TODO: still have dup logs and donot know why, maybe the dup is relevant to supervisord;
    #After fix this, remove the config excluding logs with tag _jsonparsefailure in ljinsight elasticsearch
    clear_logger_handlers(logger)
    human_handler = logging.StreamHandler(os.fdopen(sys.stdout.fileno(), 'w', 0))
    human_handler.setFormatter(ColoredFormatter(fmt='%(asctime)s [%(name)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logger.addHandler(human_handler)
    if os.getenv('VEIL_LOGGING_EVENT'):
        machine_handler = logging.StreamHandler(os.fdopen(sys.stderr.fileno(), 'w', 0))
        machine_handler.setFormatter(EventFormatter())
        logger.addHandler(machine_handler)

def clear_logger_handlers(logger):
    for h in logger.handlers:
        h.close()
    logger.handlers = []


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        record.msg = to_unicode(record.msg)
        if record.args and isinstance(record.args, dict):
            record.args = {to_unicode(k): to_unicode(v) for k, v in record.args.items()}
        s = super(ColoredFormatter, self).format(record)
        if record.levelno >= logging.WARNING:
            wrap = COLOR_WRAPPERS['RED']
        elif record.args and isinstance(record.args, dict) and record.args.get('__color__'):
            wrap = COLOR_WRAPPERS.get(record.args['__color__'])
        else:
            wrap = None
        return wrap(s) if wrap else s

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


class EventFormatter(logging.Formatter):
    def format(self, record):
        record.msg = to_unicode(record.msg)
        if record.args and isinstance(record.args, dict):
            record.args = {to_unicode(k): to_unicode(v) for k, v in record.args.items()}
        event_name = record.msg.split(':', 1)[0].strip()
        event = {
            '@type': 'veil',
            '@source': to_unicode(socket.gethostname()),
            '@message': to_unicode(record.getMessage()),
            '@timestamp': time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            '@fields': {
                'logged_by': to_unicode(record.name),
                'level': record.levelname,
                'event': event_name
            }
        }
        if record.args and isinstance(record.args, dict):
            event['@fields'].update(record.args)
        if record.exc_info:
            event['@fields']['exception_type'] = to_unicode(record.exc_info[0])
            event['@fields']['exception_stack_trace'] = to_unicode(self.formatException(record.exc_info))
        event['@fields'].update(get_log_context())
        return json.dumps(event)


log_context_providers = []

def add_log_context_provider(provider):
    log_context_providers.append(provider)

def get_log_context():
    context = {}
    for provider in log_context_providers:
        try:
            context.update(provider())
        except:
            traceback.print_exc()
    return context


def to_unicode(s):
    if isinstance(s, unicode):
        return s

    if isinstance(s, (str, bytes)):
        try:
            return unicode(s, encoding='UTF-8')
        except UnicodeDecodeError:
            try:
                return unicode(s, encoding='gb18030')
            except UnicodeDecodeError:
                return unicode(repr(s)[1:-1])

    if isinstance(s, (datetime.datetime, datetime.date, datetime.time)):
        return unicode(s.isoformat())

    if isinstance(s, tuple):
        return unicode(tuple(to_unicode(e) for e in s))

    if isinstance(s, list):
        return unicode([to_unicode(e) for e in s])

    if isinstance(s, dict):
        return unicode({to_unicode(k): to_unicode(v) for k, v in s.items()})

    try:
        return unicode(s)
    except UnicodeDecodeError:
        return unicode(repr(s))
