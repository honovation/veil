from __future__ import unicode_literals, print_function, division
from collections import OrderedDict
from veil.profile.installer import *
from ..log_shipper_setting import LOG_SHIPPER_CONF_PATH


@composite_installer
def log_shipper_resource(config):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(path=LOG_SHIPPER_CONF_PATH, content=render_config('log-shipper.cfg.j2', config=config)))
    return resources


def load_log_shipper_config():
    lines = LOG_SHIPPER_CONF_PATH.lines(encoding='UTF-8')
    config = OrderedDict()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        log_path, redis_config_line = line.split('=>')
        log_path = log_path.strip()
        redis_config_line = redis_config_line.strip()
        redis_host_port, redis_key = redis_config_line.split('/')
        redis_host, redis_port = redis_host_port.split(':')
        config[log_path] = {
            'host': redis_host,
            'port': int(redis_port),
            'key': redis_key
        }
    return objectify(config)
