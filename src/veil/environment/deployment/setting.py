from __future__ import unicode_literals, print_function, division
import sys
from veil.model.collection import *
from veil.environment.layout import *
from .filesystem import create_directory

providers = {}
pass_names = ['base', 'user', 'final']
settings = {}

def register_deployment_settings_provider(provider, pass_name='user'):
    assert pass_name in pass_names
    if settings:
        raise Exception('environment settings has already been initialized: {}'.format(settings))
    providers.setdefault(pass_name, []).append(provider)


def get_deployment_settings():
    global settings
    if not settings:
        for pass_name in pass_names:
            last_pass_settings = objectify(settings)
            for provider in providers.get(pass_name, []):
                settings = merge_settings(settings, provider(last_pass_settings))
        settings = objectify(settings)
        create_layout()
    return settings

def create_layout():
    create_directory(VEIL_HOME / 'log')
    create_directory(VEIL_LOG_DIR)
    create_directory(VEIL_HOME / 'etc')
    create_directory(VEIL_ETC_DIR)
    create_directory(VEIL_HOME / 'var')
    create_directory(VEIL_VAR_DIR)

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