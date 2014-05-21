from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

overridden_bucket_configs = {}

@composite_installer
def bucket_resource(purpose, config):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(path=VEIL_ETC_DIR / '{}-bucket.cfg'.format(purpose.replace('_', '-')),
        content=render_config('bucket.cfg.j2', config=config)))
    return resources


def override_bucket_config(purpose, **overrides):
    get_executing_test().addCleanup(overridden_bucket_configs.clear)
    overridden_bucket_configs.setdefault(purpose, {}).update(overrides)


def load_bucket_config(purpose):
    try:
        config = load_config_from(VEIL_ETC_DIR / '{}-bucket.cfg'.format(purpose.replace('_', '-')), 'type', 'base_directory', 'base_url')
    except IOError:
        if 'test' == VEIL_SERVER:
            config = DictObject()
        else:
            raise
    if 'test' == VEIL_SERVER:
        config.update(overridden_bucket_configs.get(purpose, {}))
    return config


_config = {}
def bucket_config(purpose):
    return _config.setdefault(purpose, load_bucket_config(purpose))