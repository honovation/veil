from __future__ import unicode_literals, print_function, division
from .setting import merge_settings
from .setting import get_settings

option_definitions = {}
option_updates = {}

def register_option(section, name, type=unicode):
    if type not in [unicode, int, bool]:
        raise Exception('unknown option type: {}'.format(type))
    section_option_definitions = option_definitions.setdefault(section, {})
    old_type = section_option_definitions.get(name)
    if old_type and old_type != type:
        raise Exception('{}.{} already registered as {}, can not change to {}'.format(section, name, old_type, type))
    section_option_definitions[name] = type
    return lambda: get_option(section, name)


def get_option(section, name):
    options = dict(get_settings().get('veil', None))
    options = merge_settings(options, option_updates, overrides=True)
    if not options:
        raise Exception('options have not been initialized')
    type = option_definitions.get(section, {}).get(name)
    if not type:
        raise Exception('option {}.{} has not been registered'.format(section, name))
    value = options.get(section, {}).get(name)
    if unicode == type:
        return unicode(value) if value else ''
    if int == type:
        if isinstance(value, int):
            return value
        return int(value) if value else 0
    if bool == type:
        if isinstance(value, bool):
            return value
        return 'true' == value.lower() if value else False
    raise Exception('unknown option type: {}'.format(type))


def reset_options():
    option_updates.clear()


def update_options(updates):
    from veil.development.test import get_executing_test

    get_executing_test().addCleanup(reset_options)
    option_updates.update(updates)
