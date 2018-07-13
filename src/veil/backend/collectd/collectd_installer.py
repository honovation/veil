from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *
from ..collectd_setting import COLLECTD_CONF_PATH


@composite_installer
def collectd_resource(config):
    return [
            os_package_resource(name='collectd-core'),
            file_resource(path=COLLECTD_CONF_PATH, content=render_config('collectd.conf.j2', config=config, base_dir=VEIL_BUCKETS_DIR / 'collectd'))
    ]
