from __future__ import unicode_literals, print_function, division
import functools
import logging
import sys
import inspect
import traceback
import veil_component
from veil.environment import *

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
    if 'level' in kwargs:
        level = kwargs.get('level')
    else:
        import_script_handlers(argv)
        level = script_handlers
    arg = argv[0] if argv else None
    if arg not in level:
        print('{} is unknown, choose from: {}'.format(arg, level.keys()))
        sys.exit(1)
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
    except SystemExit:
        raise
    except:
        type, value, tb = sys.exc_info()
        print(traceback.format_exc())
        print(value.message)
        sys.exit(1)

def import_script_handlers(argv):
    if argv:
        possible_module_names = []
        for i in range(len(argv)):
            if i:
                module_name = '.'.join(argv[:-i])
            else:
                module_name = '.'.join(argv)
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
        component_names = [
            'veil.backend.bucket',
            'veil.backend.database.client',
            'veil.backend.database.postgresql',
            'veil.backend.database.db2',
            'veil.backend.queue',
            'veil.backend.redis',
            'veil.development.architecture',
            'veil.development.git',
            'veil.development.loc',
            'veil.development.pycharm',
            'veil.development.test',
            'veil.development.source_code_monitor',
            'veil.environment.local_deployer',
            'veil.environment.remote_deployer',
            'veil.environment.setting',
            'veil.environment.supervisor',
            'veil.frontend.cli',
            'veil.frontend.locale',
            'veil.frontend.template',
            'veil.frontend.nginx',
            'veil.frontend.web'
        ]
        component_names.extend(get_application_components())
        for component_name in component_names:
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
    component_name = veil_component.get_loading_component_name()
    if not component_name:
        return []
    level_names = component_name.split('.')
    if level_names and 'veil' == level_names[0]:
        level_names = level_names[1:]
    return level_names

