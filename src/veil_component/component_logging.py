from __future__ import unicode_literals, print_function, division
import logging
import logging.handlers
import os
import sys
import json
import socket
from .component_map import get_root_component

VEIL_LOGGING_LEVEL_CONFIG = 'VEIL_LOGGING_LEVEL_CONFIG'
VEIL_SYSLOG_APP_NAME = 'VEIL_SYSLOG_APP_NAME'
VEIL_SYSLOG_ADDRESS = 'VEIL_SYSLOG_ADDRESS'
logging_levels = None
configured_root_loggers = set()

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
    console_handler = logging.StreamHandler(os.fdopen(sys.stderr.fileno(), 'w', 0))
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    syslog_handler = get_syslog_handler()
    if syslog_handler:
        logger.addHandler(syslog_handler)


def get_syslog_handler():
    if not os.getenv(VEIL_SYSLOG_ADDRESS):
        return None
    address = os.getenv(VEIL_SYSLOG_ADDRESS)
    if address.startswith('tcp://'):
        host, port = address.replace('tcp://', '').split(':')
        syslog_handler = logging.handlers.SysLogHandler(
            address=(host, int(port)), socktype=socket.SOCK_STREAM)
    elif address.startswith('udp://'):
        host, port = address.replace('udp://', '').split(':')
        syslog_handler = logging.handlers.SysLogHandler(
            address=(host, int(port)), socktype=socket.SOCK_DGRAM)
    else:
        syslog_handler = logging.handlers.SysLogHandler(address=address)
    syslog_handler.setFormatter(EventFormatter())
    syslog_handler.addFilter(EventFilter())
    return syslog_handler


class EventFilter(logging.Filter):
    def filter(self, record):
        return ':' in record.message


class EventFormatter(logging.Formatter):
    def format(self, record):
        event_name = record.message.split(':')[0]
        event = {
            '__category__': record.name,
            '__name__': event_name,
            '__timestamp__': record.created # sub-second accuracy
        }
        if record.args and isinstance(record.args, dict):
            event.update(record.args)
        return '{} {}[{}]: {}'.format(
            self.formatTime(record, datefmt='%b %d %H:%M:%S'),
            os.getenv(VEIL_SYSLOG_APP_NAME) or 'veil',
            os.getpid(),
            json.dumps(event))