from __future__ import unicode_literals, print_function, division
import traceback
from .setting import merge_settings
from .setting import get_settings
from veil.model.collection import *

option_definitions = {}
options = None
original_options = None

def register_option(section, name, type=unicode, default=None):
    if options is not None:
        raise Exception('options have already been initialized')
    if type not in [unicode, int, bool]:
        raise Exception('unknown option type: {}'.format(type))
    section_option_definitions = option_definitions.setdefault(section, {})
    old_type = section_option_definitions.get(name, {}).get('type')
    if old_type and old_type != type:
        raise Exception('{}.{} already registered as {}, can not change to {}'.format(section, name, old_type, type))
    section_option_definitions[name] = objectify({
        'type': type,
        'default': default,
        'defined_by': traceback.format_stack()
    })
    return lambda: get_option(section, name)


def get_option(section, name):
    init_options()
    definition = option_definitions.get(section, {}).get(name)
    if not definition:
        raise Exception('option {}.{} has not been registered'.format(section, name))
    return options[section][name]


def init_options():
    global options
    global original_options
    if options is not None:
        return
    options = dict(get_settings().get('veil', {}))
    for section, section_definitions in option_definitions.items():
        for name, definition in section_definitions.items():
            options.setdefault(section, {})
            try:
                value = decide_option_value(options[section].get(name), definition)
            except ValueError, e:
                raise Exception('option {}.{}: {}, defined by: {}'.format(
                    section, name, e.message, ''.join(definition.defined_by)))
            options[section][name] = value
    original_options = dict(options)


def decide_option_value(raw_value, definition):
    if raw_value is None and definition.default is None:
        raise ValueError('can not be empty')
    if unicode == definition.type:
        return unicode(raw_value) if raw_value else definition.default
    if int == definition.type:
        if isinstance(raw_value, int):
            return raw_value
        return int(raw_value) if raw_value else definition.default
    if bool == definition.type:
        if isinstance(raw_value, bool):
            return raw_value
        return 'true' == raw_value.lower() if raw_value else definition.default
    raise ValueError('unknown option type: {}'.format(definition.type))


def reset_options():
    options.clear()
    options.update(original_options)


def update_options(updates):
    import importlib
    test_component = importlib.import_module('veil.development.test')

    test_component.get_executing_test().addCleanup(reset_options)
    new_options = merge_settings(options, updates, overrides=True)
    options.clear()
    options.update(new_options)
