from __future__ import unicode_literals, print_function, division
import functools
from logging import getLogger
import sys
from inspect import isfunction
from sandal.component import get_loading_components
from sandal.template import *

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
            return script_handler(*args, **kwargs)

        level_names = get_current_level_names()
        level = script_handlers
        for level_name in level_names:
            if not level_name.startswith('_'):
                level = level.setdefault(level_name.replace('_', '-'), {})
        if self.command in level:
            raise Exception('{}=>{} script has already been registered'.format(
                '=>'.join(level_names), self.command))
        level[self.command] = wrapper
        return script_handler


def get_current_level_names():
    components = get_loading_components()
    if not components:
        return []
    component = components[-1]
    level_names = component.__name__.split('.')
    if component.__name__.startswith('veil.'):
        level_names = level_names[1:]
    return level_names