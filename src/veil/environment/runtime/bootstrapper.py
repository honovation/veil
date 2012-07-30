from __future__ import unicode_literals, print_function, division
import logging
from veil.model.test import *
from .option import register_option
from .option import init_options

LOGGER = logging.getLogger(__name__)

@test_bootstrapper
def bootstrap_runtime():
    import sys
    import os.path

    __dir__ = os.path.dirname(__file__)
    if __dir__ in sys.path:
        sys.path.remove(__dir__) # disable old style relative import

    import logging
    from ConfigParser import RawConfigParser
    from veil.component import scan_components
    from veil.model.event import subscribe_event
    from veil.model.const import consts
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
    veil_cfg = VEIL_ETC_DIR / 'veil.cfg'
    executing_test = get_executing_test(optional=True)
    if executing_test and not veil_cfg.exists():
        raise Exception('{} not exists'.format(veil_cfg))
    config_parser.read(veil_cfg)
    options = {}
    for section in config_parser.sections():
        options[section] = dict(config_parser.items(section))
    if options:
        if executing_test and hasattr(executing_test, 'options'):
            options.update(executing_test.options)
        init_options(options)
    else:
        LOGGER.warn('options is empty')