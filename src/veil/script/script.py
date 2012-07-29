from __future__ import unicode_literals, print_function, division
from ConfigParser import RawConfigParser
import functools
from logging import getLogger
import sys
from inspect import isfunction
from sandal.component import get_loading_components
from sandal.template import *
from sandal.option import *
from veil.layout import *

script_handlers = {}
LOGGER = getLogger(__name__)

def execute_script(argv, level=None):
    level = level or script_handlers
    arg = argv[0] if argv else None
    if arg not in level:
        LOGGER.error('{} is unknown, choose from: {}'.format(arg, level.keys()))
        sys.exit(1)
    next_level = level[arg]
    if isfunction(next_level):
        script_handler = next_level
        with require_current_template_directory_relative_to(script_handler):
            return script_handler(*argv[1:])
    else:
        return execute_script(argv[1:], next_level)


def script(command):
# syntax sugar for ScriptHandlerDecorator
    return ScriptHandlerDecorator(command)


class ScriptHandlerDecorator(object):
    def __init__(self, command):
        self.command = command

    def __call__(self, script_handler):
        @functools.wraps(script_handler)
        def wrapper(*args, **kwargs):
            self.load_options()
            return script_handler(*args, **kwargs)
        component = get_loading_components()[-1]
        level_names = component.__name__.split('.')
        if component.__name__.startswith('veil.'):
            level_names = level_names[1:]
        level = script_handlers
        for level_name in level_names:
            if not level_name.startswith('_'):
                level = level.setdefault(level_name.replace('_', '-'), {})
        if self.command in level:
            raise Exception('{}=>{} script has already been registered'.format(
                '=>'.join(level_names), self.command))
        level[self.command] = wrapper
        return script_handler

    def load_options(self):
        config_parser = RawConfigParser()
        config_parser.read(VEIL_ETC_DIR / 'veil.cfg')
        options = {}
        for section in config_parser.sections():
            options[section] = dict(config_parser.items(section))
        init_options(options)