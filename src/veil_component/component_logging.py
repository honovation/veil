import logging
import os
import sys
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
    veil_log_config_file = os.getenv('VEIL_LOG')
    if not veil_log_config_file:
        return
    with open(veil_log_config_file) as f:
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
    handler = logging.StreamHandler(os.fdopen(sys.stderr.fileno(), 'w', 0))
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger = logging.getLogger(component_name)
    logger.addHandler(handler)