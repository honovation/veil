from __future__ import unicode_literals, print_function, division
import sys
import traceback
import importlib
from veil.model.collection import *
from veil.environment import *

initialized_by = None
overridden_test_settings = None
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
    if 'test' == VEIL_SERVER:
        return merge_settings(settings, overridden_test_settings or {}, overrides=True)
    else:
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


def override_test_settings(settings):
    assert 'test' == VEIL_SERVER, 'can only override settings in test mode'
    global overridden_test_settings

    def reset_overridden_test_settings():
        overridden_test_settings = None

    test_component = importlib.import_module('veil.development.test')
    test_component.get_executing_test().addCleanup(reset_overridden_test_settings)
    overridden_test_settings = merge_settings(overridden_test_settings or {}, settings, overrides=True)