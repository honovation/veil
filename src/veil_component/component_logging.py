import logging
import logging.handlers
import socket
import os
import sys
import json
from .component_map import get_root_component

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
    veil_logging_level_config = os.getenv('VEIL_LOGGING_LEVEL_CONFIG')
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
    console_handler = logging.StreamHandler(os.fdopen(sys.stderr.fileno(), 'w', 0))
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#    syslog_handler = logging.handlers.SysLogHandler(
#        address='/dev/veil-log',
#        facility=logging.handlers.SysLogHandler.LOG_USER)
#    syslog_handler.setFormatter(EventFormatter())
#    syslog_handler.addFilter(EventFilter())
    logger = logging.getLogger(component_name)
    logger.addHandler(console_handler)
#    logger.addHandler(syslog_handler)

class EventFilter(logging.Filter):
    def filter(self, record):
        return ':' in record.message

class EventFormatter(logging.Formatter):
    def format(self, record):
        event_name = record.message.split(':')[0]
        event = {'__category__': record.name, '__name__': event_name}
        if record.args and isinstance(record.args, dict):
            event.update(record.args)
        return json.dumps(event)