import logging
import os
import sys
from .component_map import get_root_component

veil_log_configured = False
configured_root_loggers = set()

def configure_logging(component_name):
    veil_log_config_file = os.getenv('VEIL_LOG')
    if veil_log_config_file:
        configure_by_file(veil_log_config_file)
    else:
        configure_component_logger(component_name, logging.DEBUG)


def configure_by_file(config_file):
    global veil_log_configured
    if veil_log_configured:
        return
    veil_log_configured = True
    with open(config_file) as f:
        lines = f.readlines()
    for line in lines:
        logger_name, logging_level = line.split('=')
        logging_level = getattr(logging, logging_level.strip())
        configure_component_logger(logger_name, logging_level)


def configure_component_logger(component_name, logging_level):
    logger = logging.getLogger(component_name)
    logger.setLevel(logging_level)
    configure_root_component_logger(get_root_component(component_name))


def configure_root_component_logger(component_name):
    if component_name in configured_root_loggers:
        return
    configured_root_loggers.add(component_name)
    handler = logging.StreamHandler(os.fdopen(sys.stderr.fileno(), 'w', 0))
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger = logging.getLogger(component_name)
    logger.addHandler(handler)