from __future__ import unicode_literals, print_function, division
import sys
from veil.model.collection import *

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
            key, value = [x.strip() for x in line.split('=')]
            config[key] = value
    assert set(expected_keys) == set(config.keys()),\
    'config file {} does not provide exact keys we want, expected: {}, actual: {}'.format(
        path, set(expected_keys), set(config.keys()))
    return config