from __future__ import unicode_literals, print_function, division
from logging import getLogger
from sandal.component import get_loading_components
from inspect import isfunction

script_handlers = {}
LOGGER = getLogger(__name__)

def execute_script(argv, level=None):
    if not level:
        LOGGER.info('* executing script: {}'.format(' '.join(argv)))
    level = level or script_handlers
    arg = argv[0] if argv else None
    if arg not in level:
        raise Exception('{} is unknown, choose from: {}'.format(arg, level.keys()))
    next_level = level[arg]
    if isfunction(next_level):
        script_handler = next_level
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
        level = script_handlers
        for component_name in component_hierarchy_names[1:]:
            if not component_name.startswith('_'):
                level = level.setdefault(component_name.replace('_', '-'), {})
        if self.command in level:
            raise Exception('{}=>{} script has already been registered'.format(
                '=>'.join(component_hierarchy_names), self.command))
        level[self.command] = script_handler
        return script_handler