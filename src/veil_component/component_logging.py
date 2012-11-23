import logging
import os
import sys

veil_log_configured = False
configured_loggers = set()

def configure_logging(component_name):
    veil_log_config_file = os.getenv('VEIL_LOG')
    if veil_log_config_file:
        configure_by_file(veil_log_config_file)
    else:
        configure_logger(component_name, logging.DEBUG)


def configure_by_file(config_file):
    global veil_log_configured
    if veil_log_configured:
        return
    veil_log_configured = True
    with open(config_file) as f:
        lines = f.readlines()
    logging_levels = {}
    for line in lines:
        logger_name, logging_level = line.split('=')
        logging_level = getattr(logging, logging_level.strip())
        logging_levels[logger_name] = logging_level
    for logger_name in sorted(logging_levels.keys()):
        configure_logger(logger_name, logging_levels[logger_name])


def configure_logger(logger_name, logging_level):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging_level)
    if logger_name in configured_loggers:
        return
    for configured_component_name in configured_loggers:
        if logger_name.startswith('{}.'.format(configured_component_name)):
            return
        if configured_component_name.startswith('{}.'.format(logger_name)):
            print('component logging init order is wrong: {}, {}'.format(logger_name, configured_component_name))
    configured_loggers.add(logger_name)
    handler = logging.StreamHandler(os.fdopen(sys.stderr.fileno(), 'w', 0))
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)