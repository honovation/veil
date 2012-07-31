from __future__ import unicode_literals, print_function, division
from veil.model.event import publish_event
from sandal.test import *

EVENT_OPTIONS_INITIALIZED = 'options-initialized'
option_definitions = {}
options = {}
original_options = {}

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
    if not options:
        raise Exception('options have not been initialized')
    type = option_definitions.get(section, {}).get(name)
    if not type:
        raise Exception('option {}.{} has not been registered'.format(section, name))
    value = options.get(section, {}).get(name)
    if unicode == type:
        return unicode(value) if value else ''
    if int == type:
        return int(value) if value else 0
    if bool == type:
        return 'true' == value.lower() if value else False
    raise Exception('unknown option type: {}'.format(type))


def init_options(configured_options):
    if not configured_options:
        raise Exception('options is empty')
    if options:
        raise Exception('options already initialized')
    options.update(configured_options)
    original_options.update(configured_options)
    publish_event(EVENT_OPTIONS_INITIALIZED)


def reset_options():
    options.clear()
    options.update(original_options)


def update_options(updates):
    get_executing_test().addCleanup(reset_options)
    options.update(updates)
