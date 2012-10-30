from __future__ import unicode_literals, print_function, division
import functools
import logging
import sys
import inspect
import traceback
from veil_component import get_loading_component, assert_component_loaded
from veil.environment.setting import *

script_handlers = {}
LOGGER = logging.getLogger(__name__)
executing_script_handlers = []

def is_script_defined(*argv):
    current_level = script_handlers
    for arg in argv:
        current_level = current_level.get(arg, None)
        if not current_level:
            return False
    return True


def execute_script(*argv, **kwargs):
    level = kwargs.get('level', script_handlers)
    arg = argv[0] if argv else None
    if arg not in level:
        print('{} is unknown, choose from: {}'.format(arg, level.keys()))
        sys.exit(1)
    try:
        next_level = level[arg]
        if inspect.isfunction(next_level):
            script_handler = next_level
            bootstrap_runtime()
            try:
                executing_script_handlers.append(script_handler)
                return script_handler(*argv[1:])
            finally:
                executing_script_handlers.pop()
        else:
            return execute_script(level=next_level, *argv[1:])
    except SystemExit:
        raise
    except:
        formatted_exception = traceback.format_exc()
        try:
            if not 'install' in argv:
                exception = sys.exc_info()[1]
                if not hasattr(exception, 'EXECUTABLE_BEFORE_COMPONENT_LOADED'):
                    import __veil__
                    for component_name in getattr(__veil__, 'COMPONENTS', []):
                        assert_component_loaded(component_name)
        except:
            pass
        finally:
            print(formatted_exception)
        sys.exit(1)

def get_executing_script_handler():
    if executing_script_handlers:
        return executing_script_handlers[-1]
    else:
        return None


def script(command):
# syntax sugar for ScriptHandlerDecorator
    return ScriptHandlerDecorator(command)


class ScriptHandlerDecorator(object):
    def __init__(self, command):
        self.command = command

    def __call__(self, script_handler):
        script_handler = script_handler

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
    component = get_loading_component()
    if not component:
        return []
    level_names = component.__name__.split('.')
    if level_names and 'veil' == level_names[0]:
        level_names = level_names[1:]
    return level_names

