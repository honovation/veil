from __future__ import unicode_literals, print_function, division
import sys
from veil.model.collection import *

initialized = False
settings = {}
coordinators = []

def add_settings(additional_settings, overrides=False):
    global settings
    if initialized:
        raise Exception('settings has already been initialized: {}'.format(settings))
    settings = merge_settings(settings, additional_settings, overrides=overrides)


def register_settings_coordinator(coordinator):
    coordinators.append(coordinator)


def get_settings():
    global initialized
    global settings
    if not initialized:
        initialized = True
        settings = objectify(settings)
    for coordinator in coordinators:
        settings = coordinator(settings)
        if not isinstance(settings, DictObject):
            raise Exception('{} should return DictObject'.format(coordinator))
    return settings


def merge_settings(base, updates, overrides=False):
    if not base:
        return updates
    if isinstance(base, dict) and isinstance(updates, dict):
        updated = DictObject()
        for k, v in base.items():
            try:
                updated[k] = merge_settings(v, updates.get(k), overrides=overrides)
            except:
                raise Exception('can not merge: {}\r\n{}'.format(k, sys.exc_info()[1]))
        for k, v in updates.items():
            if k not in updated:
                updated[k] = v
        return updated
    if base == updates:
        return base
    if updates:
        if overrides:
            return updates
        else:
            raise Exception('can not merge {} with {}'.format(base, updates))
    return base