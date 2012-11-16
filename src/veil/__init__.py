from .environment import VEIL_SERVER

def configure_logging(logger_name, logging_level):
    import logging
    import os
    import sys

    LOGGING_LEVEL_VALUES = {}
    for level in [logging.DEBUG, logging.INFO, logging.WARN, logging.ERROR, logging.CRITICAL]:
        LOGGING_LEVEL_VALUES[logging.getLevelName(level)] = level
    level = LOGGING_LEVEL_VALUES[logging_level]
    handler = logging.StreamHandler(os.fdopen(sys.stderr.fileno(), 'w', 0))
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.addHandler(handler)

configure_logging(__name__, 'DEBUG')