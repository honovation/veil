from __future__ import unicode_literals, print_function, division
import sys
from sandal.collection import *
from .layout import create_layout

providers = []
env_settings = {}

def register_environment_settings_provider(provider):
    if env_settings:
        raise Exception('environment settings has already been initialized: {}'.format(env_settings))
    providers.append(provider)


def get_environment_settings():
    global env_settings
    if not env_settings:
        for provider in providers:
            settings = provider()
            env_settings = merge_settings(env_settings, settings)
        env_settings = objectify(env_settings)
        create_layout()
    return env_settings


def merge_settings(base, updates):
    if not base:
        return updates
    if isinstance(base, dict) and isinstance(updates, dict):
        updated = {}
        for k, v in base.items():
            try:
                updated[k] = merge_settings(v, updates.get(k))
            except:
                raise Exception('can not merge: {}\r\n{}'.format(k, sys.exc_info[1]))
        for k, v in updates.items():
            if k not in updated:
                updated[k] = v
        return updated
    if updates:
        raise Exception('can not merge {} with {}'.format(base, updates))
    return base