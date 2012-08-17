from __future__ import unicode_literals, print_function, division
from .setting import merge_settings
from .setting import get_settings
from veil.model.collection import *

option_definitions = {}
option_updates = {}

def register_option(section, name, type=unicode, default=None):
    if type not in [unicode, int, bool]:
        raise Exception('unknown option type: {}'.format(type))
    section_option_definitions = option_definitions.setdefault(section, {})
    old_type = section_option_definitions.get(name, {}).get('type')
    if old_type and old_type != type:
        raise Exception('{}.{} already registered as {}, can not change to {}'.format(section, name, old_type, type))
    if default is None:
        if unicode == type:
            default = ''
        elif int == type:
            default = 0
        elif bool == type:
            default = False
        else:
            raise NotImplementedError('{} type is not supported'.format(type))
    section_option_definitions[name] = objectify({
        'type': type,
        'default': default
    })
    return lambda: get_option(section, name)


def get_option(section, name):
    options = dict(get_settings().get('veil', None))
    options = merge_settings(options, option_updates, overrides=True)
    if not options:
        raise Exception('options have not been initialized')
    definition = option_definitions.get(section, {}).get(name)
    if not definition:
        raise Exception('option {}.{} has not been registered'.format(section, name))
    value = options.get(section, {}).get(name)
    if unicode == definition.type:
        return unicode(value) if value else definition.default
    if int == definition.type:
        if isinstance(value, int):
            return value
        return int(value) if value else definition.default
    if bool == definition.type:
        if isinstance(value, bool):
            return value
        return 'true' == value.lower() if value else definition.default
    raise Exception('unknown option type: {}'.format(definition.type))


def reset_options():
    option_updates.clear()


def update_options(updates):
    from veil.development.test import get_executing_test

    get_executing_test().addCleanup(reset_options)
    option_updates.update(updates)
