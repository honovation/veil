from __future__ import unicode_literals, print_function, division
import sys
import traceback
from veil.model.collection import *

initialized_by = None
settings = None
coordinators = []


def register_settings_coordinator(coordinator):
    if initialized_by:
        raise Exception('settings has already been initialized by: {}'.format(initialized_by))
    coordinators.append(coordinator)


def get_settings():
    __import__('__veil__')
    if not initialized_by:
        raise Exception('settings has not been initialized yet')
    return settings


def initialize_settings(*multiple_settings):
    global initialized_by
    global settings
    if initialized_by:
        raise Exception('settings has already been initialized by: {}'.format(initialized_by))
    initialized_by = str('\n').join(traceback.format_stack())
    settings = merge_settings(settings, merge_multiple_settings(*multiple_settings))
    for coordinator in coordinators:
        settings = coordinator(settings)
        if not isinstance(settings, DictObject):
            raise Exception('{} should return DictObject'.format(coordinator))
    settings = freeze_dict_object(settings)
    return settings


def merge_multiple_settings(*multiple_settings):
    merged_settings = {}
    for settings in multiple_settings:
        merged_settings = merge_settings(merged_settings, settings)
    return merged_settings


def merge_settings(base, updates, overrides=False):
    if base is None:
        return freeze_dict_object(updates)
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
        return freeze_dict_object(updated)
    if base == updates:
        return freeze_dict_object(base)
    if updates is not None:
        if overrides:
            return updates
        else:
            raise Exception('can not merge {} with {}'.format(base, updates))
    return freeze_dict_object(base)


def load_config_from(path, *expected_keys):
    config = DictObject()
    with open(path) as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            key, value = line.split('=')
            config[key] = value
    assert set(expected_keys) == set(config.keys()),\
    'config file {} does not provide exact keys we want, expected: {}, actual: {}'.format(
        path, expected_keys, config.keys())
    return config