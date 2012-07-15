from __future__ import unicode_literals, print_function, division
from logging import getLogger
import sys
from sandal.component import get_loading_components
from inspect import isfunction
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
        component = get_loading_components()[-1]
        component_hierarchy_names = component.__name__.split('.')
        if component.__name__.startswith('veil.'):
            component_hierarchy_names = component_hierarchy_names[1:]
        level = script_handlers
        for component_name in component_hierarchy_names:
            if not component_name.startswith('_'):
                level = level.setdefault(component_name.replace('_', '-'), {})
        if self.command in level:
            raise Exception('{}=>{} script has already been registered'.format(
                '=>'.join(component_hierarchy_names), self.command))
        level[self.command] = script_handler
        return script_handler