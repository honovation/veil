from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *
from veil.backend.log_rotater_setting import LOG_ROTATER_CONF_PATH


@composite_installer
def log_rotater_resource(config):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(os_package_resource(name='logrotate'))
    resources.append(
        file_resource(path=LOG_ROTATER_CONF_PATH, content=render_config('log-rotater.cfg.j2', config=config)))
    return resources