from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *
from veil.backend.collectd_setting import COLLECTD_CONF_PATH


@composite_installer
def collectd_resource(config):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        os_package_resource(name='collectd-core'),
        file_resource(path=COLLECTD_CONF_PATH, content=render_config('collectd.conf.j2', config=config, base_dir=VEIL_VAR_DIR / 'collectd'))
    ])
    return resources