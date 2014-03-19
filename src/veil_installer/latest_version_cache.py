"""
serves as cache to speed up upgrade decision
"""
from __future__ import unicode_literals, print_function, division
from veil.env_const import VEIL_ENV_TYPE
from veil_component import VEIL_HOME

RESOURCE_LATEST_VERSION = VEIL_HOME / 'RESOURCE-LATEST-VERSION'
RESOURCE_LATEST_VERSION_TEST = VEIL_HOME / 'RESOURCE-LATEST-VERSION-TEST'

version_cache = {'development': None, 'test': None}


def set_resource_latest_version(key, version):
    assert VEIL_ENV_TYPE in ('development', 'test')
    assert version, 'key={}, version={}'.format(key, version)
    load_all()
    if VEIL_ENV_TYPE == 'development' or key in version_cache['development']:
        version_cache['development'][key] = version
    version_cache['test'][key] = version
    save_all()


def get_resource_latest_version(key):
    load_all()
    if VEIL_ENV_TYPE == 'test':
        return version_cache['test'].get(key)
    else:
        if VEIL_ENV_TYPE == 'development' and key not in version_cache['development'] and key in version_cache['test']:
            version_cache['development'][key] = version_cache['test'][key]
            save_all()
        return version_cache['development'].get(key)


def load_all():
    global version_cache
    if version_cache['development'] is None:
        if RESOURCE_LATEST_VERSION.exists():
            version_cache['development'] = dict(line.split('=') for line in RESOURCE_LATEST_VERSION.text().splitlines(False))
        else:
            version_cache['development'] = {}
    if version_cache['test'] is None:
        if RESOURCE_LATEST_VERSION_TEST.exists():
            version_cache['test'] = dict(line.split('=') for line in RESOURCE_LATEST_VERSION_TEST.text().splitlines(False))
        else:
            version_cache['test'] = {}


def save_all():
    RESOURCE_LATEST_VERSION.write_text(
        '\n'.join('{}={}'.format(key, version_cache['development'][key]) for key in sorted(version_cache['development'].keys())))
    RESOURCE_LATEST_VERSION_TEST.write_text(
        '\n'.join('{}={}'.format(key, version_cache['test'][key]) for key in sorted(version_cache['test'].keys())))