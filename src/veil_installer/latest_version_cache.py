from __future__ import unicode_literals, print_function, division
from veil_component import *

RESOURCE_LATEST_VERSION = VEIL_HOME / 'RESOURCE-LATEST-VERSION'

# this serves as cache to speed up upgrade decision

def set_resource_latest_version(key, version):
    assert version
    updated = list_all()
    updated[key] = version
    save_all(updated)


def get_resource_latest_version(key):
    return list_all().get(key)


def list_all():
    if not RESOURCE_LATEST_VERSION.exists():
        return {}
    return dict(line.split('=') for line in RESOURCE_LATEST_VERSION.text().splitlines(False))


def save_all(versions):
    RESOURCE_LATEST_VERSION.write_text('\n'.join(['{}={}'.format(key, versions[key]) for key in sorted(versions.keys())]))