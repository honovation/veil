from __future__ import unicode_literals, print_function, division
import functools
import logging
import sys
import inspect
from veil_component import *
from veil.utility.tracing import *
from veil.utility.encoding import *
from veil.model.event import *
from veil.server.process import *

LOGGER = logging.getLogger(__name__)
script_handlers = {}
executing_script_handlers = []


def is_script_defined(*argv):
    current_level = script_handlers
    for arg in argv:
        current_level = current_level.get(arg)
        if not current_level:
            return False
    return True


def execute_script(*argv):
    if VEIL_ENV_TYPE in {'development', 'test'}:
        start_recording_dynamic_dependencies()
    argv = [to_unicode(arg) for arg in argv]
    import_script_handlers(argv)
    # after components loaded, so necessary event handlers installed
    publish_event(EVENT_PROCESS_SETUP, loads_event_handlers=False)
    level = script_handlers
    execute_script_at_level(level, argv)


def execute_script_at_level(level, argv):
    arg = argv[0] if argv else None
    if arg not in level:
        LOGGER.warn('unknown option found: unknown_option=%(unknown_option)s, valid_options=%(valid_options)s', {
            'unknown_option': arg,
            'valid_options': level.keys(),
        })
        sys.exit(1)
    next_level = level[arg]
    if inspect.isfunction(next_level):
        script_handler = next_level
        try:
            executing_script_handlers.append(script_handler)
            try:
                return script_handler(*argv[1:])
            except KeyboardInterrupt:
                LOGGER.info('script terminated by KeyboardInterrupt: %(script_handler)s %(argv)s', {
                    'script_handler': script_handler,
                    'argv': argv
                })
                return
        finally:
            executing_script_handlers.pop()
    else:
        return execute_script_at_level(next_level, argv[1:])


def import_script_handlers(argv):
    if argv:
        possible_module_names = []
        for i in range(len(argv)):
            if i:
                module_name = to_unicode(b'.'.join(argv[:-i]))
            else:
                module_name = to_unicode(b'.'.join(argv))
            module_name = module_name.replace('-', '_')
            possible_module_names.append(module_name)
            possible_module_names.append('veil.{}'.format(module_name))
        for module_name in possible_module_names:
            try:
                __import__(module_name)
            except Exception:
                if find_module_loader_without_import(module_name):
                    raise
    if not script_handlers:
        for component_name in (list_all_components()):
            try:
                __import__(component_name)
            except Exception:
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
            raise Exception('{}=>{} script has already been registered'.format('=>'.join(level_names), self.command))
        level[self.command] = wrapper
        return script_handler


def get_current_level_names():
    component_name = get_loading_component_name()
    if not component_name:
        return []
    level_names = component_name.split('.')
    if level_names and 'veil' == level_names[0]:
        level_names = level_names[1:]
    return level_names


def ask_for_confirmation(prompt, default_answer=False):
    """
    prompts for yes or no response from the user. Returns True for yes and False for no.
    default_answer is assumed by the caller when user simply types ENTER.
    """
    if default_answer:
        prompt = '{} [{}]|{}: '.format(prompt, 'Y', 'N')
    else:
        prompt = '{} {}|[{}]: '.format(prompt, 'Y', 'N')
    while True:
        answer = raw_input(prompt)
        if not answer:
            return default_answer
        if answer not in ('Y', 'N'):
            print('Please enter Y or N')
            continue
        return answer == 'Y'
