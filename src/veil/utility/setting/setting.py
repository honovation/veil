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
    if updates is None or base == updates:
        return freeze_dict_object(base)
    if isinstance(base, dict) and isinstance(updates, dict):
        merged = DictObject()
        for k in base:
            if k in updates:
                try:
                    merged[k] = merge_settings(base[k], updates[k], overrides=overrides)
                except:
                    raise Exception('can not merge: {}\r\n{}'.format(k, sys.exc_info()[1]))
            else:
                merged[k] = base[k]
        for k in updates:
            if k not in merged:
                merged[k] = updates[k]
        return freeze_dict_object(merged)
    if overrides:
        return freeze_dict_object(updates)
    else:
        raise Exception('can not merge {} with {}'.format(base, updates))


def load_config_from(path, *required_keys):
    config = DictObject()
    with open(path) as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            key, value = [x.strip() for x in line.split('=', 1)]
            config[key] = value
    assert set(required_keys) <= set(config), 'config file {} does not provide exact required keys we want, expected: {}, actual: {}'.format(
        path, set(required_keys), set(config))
    return config