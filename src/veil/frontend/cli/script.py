from __future__ import unicode_literals, print_function, division
import functools
import logging
import sys
import inspect
import traceback
import veil_component
from veil.environment import *
from veil.utility.tracing import *
from veil.utility.encoding import *

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
    if VEIL_ENV in ['test', 'development']:
        veil_component.start_recording_dynamic_dependencies()
    argv = [to_unicode(arg) for arg in argv]
    if 'level' in kwargs:
        level = kwargs.get('level')
    else:
        import_script_handlers(argv)
        level = script_handlers
    arg = argv[0] if argv else None
    if arg not in level:
        LOGGER.warn(
            '%(unknown_option)s is unknown, choose from: %(valid_options)s', {
                'unknown_option': arg,
                'valid_options': level.keys(),
            })
        sys.exit(1)
    script_handler = None
    try:
        next_level = level[arg]
        if inspect.isfunction(next_level):
            script_handler = next_level
            try:
                executing_script_handlers.append(script_handler)
                return script_handler(*argv[1:])
            finally:
                executing_script_handlers.pop()
        else:
            return execute_script(level=next_level, *argv[1:])
    except KeyboardInterrupt:
        LOGGER.info('script terminated by KeyboardInterrupt: %(script_handler)s %(argv)s', {
            'script_handler': script_handler,
            'argv': argv
        })
        return
    except SystemExit:
        raise
    except:
        type, value, tb = sys.exc_info()
        LOGGER.error(traceback.format_exc())
        LOGGER.error(value.message)
        sys.exit(1)


def import_script_handlers(argv):
    if argv:
        possible_module_names = []
        for i in range(len(argv)):
            if i:
                module_name = to_unicode(str('.').join(argv[:-i]))
            else:
                module_name = to_unicode(str('.').join(argv))
            module_name = module_name.replace('-', '_')
            possible_module_names.append(module_name)
            possible_module_names.append('veil.{}'.format(module_name))
        for module_name in possible_module_names:
            try:
                __import__(module_name)
            except:
                if veil_component.find_module_loader_without_import(module_name):
                    raise
                else:
                    pass
    if not script_handlers:
        for component_name in (list_all_components()):
            try:
                __import__(component_name)
            except:
                pass


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
        script_handler = traced(color='GREEN')(script_handler)

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
    component_name = veil_component.get_loading_component_name()
    if not component_name:
        return []
    level_names = component_name.split('.')
    if level_names and 'veil' == level_names[0]:
        level_names = level_names[1:]
    return level_names

