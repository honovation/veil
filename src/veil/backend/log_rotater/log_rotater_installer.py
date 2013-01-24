from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


@composite_installer
def log_rotater_resource(config):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(os_package_resource(name='logrotate'))
    resources.append(
        file_resource(path=config.pop('config_file'), content=render_config(
            'log-rotater.cfg.j2', config=config)))
    return resources