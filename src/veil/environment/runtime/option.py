from __future__ import unicode_literals, print_function, division
from sandal.event import publish_event
from sandal.const import consts
from sandal.collection import *

consts.EVENT_OPTIONS_INITIALIZED = 'options-initialized'
option_definitions = {}
options = {}

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
    if value is None:
        if int == type:
            return 0
        elif bool == type:
            return False
        else:
            return None
    if unicode == type:
        return unicode(value)
    if int == type:
        return int(value)
    if bool == type:
        return 'true' == value.lower()
    raise Exception('unknown option type: {}'.format(type))


def init_options(configured_options):
    if not configured_options:
        raise Exception('options is empty')
    if options:
        raise Exception('options already initialized')
    options.update(configured_options)
    publish_event(consts.EVENT_OPTIONS_INITIALIZED)


def reset_options():
    options.clear()


def peek_options():
    return objectify(options)
