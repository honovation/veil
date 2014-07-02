from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


def register_http_service_config(purpose, *required_keys):
    add_application_sub_resource('{}_http_service'.format(purpose), lambda config: http_service_resource(purpose=purpose, **config))
    return lambda: http_service_config(purpose, *required_keys)


@composite_installer
def http_service_resource(purpose, **config):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(path=VEIL_ETC_DIR / '{}-http-service.cfg'.format(purpose.replace('_', '-')),
        content=render_config('http-service.cfg.j2', config=config)))
    return resources


def load_http_service_config(purpose, *required_keys):
    return load_config_from(VEIL_ETC_DIR / '{}-http-service.cfg'.format(purpose.replace('_', '-')), *required_keys)


_config = {}
def http_service_config(purpose, *required_keys):
    return _config.setdefault(purpose, load_http_service_config(purpose, *required_keys))