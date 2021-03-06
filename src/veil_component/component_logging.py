from __future__ import unicode_literals, print_function, division
import datetime
import logging
import os
import sys
import json
import time
import socket
import traceback

from .environment import VEIL_ENV
from .colors import red, green
from .component_map import get_root_component

VEIL_LOGGING_LEVEL_CONFIG = 'VEIL_LOGGING_LEVEL_CONFIG'
VEIL_LOGGING_EVENT = 'VEIL_LOGGING_EVENT'

logging_levels = None
configured_root_loggers = set()
log_context_providers = []


def configure_logging(component_name):
    if '.' in component_name:
        root_package = component_name.split('.', 1)[0]
        if root_package and root_package not in configured_root_loggers:
            configure_logging(root_package)
    logger = logging.getLogger(component_name)
    logger.setLevel(get_logging_level(component_name))
    clear_logger_handlers(logger)
    configure_root_component_logger(get_root_component(component_name) or component_name)


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
    for component_name in logging_levels:
        if target == component_name or target.startswith('{}.'.format(component_name)):
            matched_component_names.append(component_name)
    if not matched_component_names:
        return logging_levels.get('__default__', logging.DEBUG if VEIL_ENV.is_dev or VEIL_ENV.is_test else logging.INFO)
    return logging_levels[max(matched_component_names)]


def configure_root_component_logger(root_component_name):
    if root_component_name in configured_root_loggers:
        return
    configured_root_loggers.add(root_component_name)
    logger = logging.getLogger(root_component_name)
    logger.propagate = False
    human_handler = logging.StreamHandler(sys.stdout)
    human_handler.setFormatter(ColoredFormatter(fmt='%(asctime)s [%(name)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logger.addHandler(human_handler)
    if os.getenv('VEIL_LOGGING_EVENT'):
        machine_handler = logging.StreamHandler(sys.stderr)
        machine_handler.setFormatter(EventFormatter())
        logger.addHandler(machine_handler)


def clear_logger_handlers(logger):
    for h in logger.handlers:
        h.close()
    logger.handlers = []


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        record.msg = to_unicode(record.msg)
        log_context = get_log_context()
        old_record_msg = None
        try:
            if log_context and any(log_context[k] for k in log_context):
                old_record_msg = record.msg
                record.msg = '{}, LOG CONTEXT: {}'.format(record.msg, log_context)
            if record.args and isinstance(record.args, dict):
                record.args = {to_unicode(k): to_unicode(v) for k, v in record.args.items()}
            s = super(ColoredFormatter, self).format(record)
        finally:
            if old_record_msg:
                record.msg = old_record_msg
        if record.levelno >= logging.WARNING:
            wrap = COLOR_WRAPPERS['RED']
        elif record.args and isinstance(record.args, dict) and record.args.get('__color__'):
            wrap = COLOR_WRAPPERS.get(record.args['__color__'])
        else:
            wrap = None
        return wrap(s) if wrap else s

COLOR_WRAPPERS = {
    'RED': red,
    'GREEN': green
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
            '@timestamp': time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(record.created)),
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


def add_log_context_provider(provider):
    log_context_providers.append(provider)


def get_log_context():
    context = {}
    for provider in log_context_providers:
        try:
            context.update(provider())
        except Exception:
            traceback.print_exc()
    # escape % in value of log context otherwise it breaks format syntax (record.msg % record.args) in record.getMessage()
    return {k: v.replace('%', '%%') if isinstance(v, basestring) else v for k, v in context.items()}


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
        return unicode(repr(s)[1:-1])
