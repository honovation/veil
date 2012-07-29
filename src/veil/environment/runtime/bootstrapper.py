from __future__ import unicode_literals, print_function, division
from .option import register_option
from .option import init_options

def bootstrap_runtime():
    import sys
    import os.path

    __dir__ = os.path.dirname(__file__)
    if __dir__ in sys.path:
        sys.path.remove(__dir__) # disable old style relative import

    import logging
    from ConfigParser import RawConfigParser
    from sandal.component import scan_components
    from sandal.event import subscribe_event
    from sandal.const import consts
    from veil.environment.layout import VEIL_HOME
    from veil.environment.layout import VEIL_ETC_DIR


    get_logging_level = register_option('logging', 'level')

    handler = logging.StreamHandler(os.fdopen(sys.stderr.fileno(), 'w', 0))
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    def configure_logging(logging_level=None):
        LOGGING_LEVEL_VALUES = {}
        for level in [logging.DEBUG, logging.INFO, logging.WARN, logging.ERROR, logging.CRITICAL]:
            LOGGING_LEVEL_VALUES[logging.getLevelName(level)] = level
        level = LOGGING_LEVEL_VALUES[logging_level or get_logging_level() or 'INFO']
        logger = logging.getLogger()
        logger.setLevel(level)
        logger.addHandler(handler)

    configure_logging('INFO')
    subscribe_event(consts.EVENT_OPTIONS_INITIALIZED, configure_logging)

    for component_name in scan_components(VEIL_HOME / 'src'):
        __import__(component_name)

    config_parser = RawConfigParser()
    config_parser.read(VEIL_ETC_DIR / 'veil.cfg')
    options = {}
    for section in config_parser.sections():
        options[section] = dict(config_parser.items(section))
    init_options(options)