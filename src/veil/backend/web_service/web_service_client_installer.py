from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment import *
from veil.utility.setting import *

@composite_installer
def web_service_client_resource(purpose, url):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(
        file_resource(path=VEIL_ETC_DIR / '{}-web-service.cfg'.format(purpose.replace('_', '-')), content=render_config(
            'web-service-client.cfg.j2', url=url)))
    return resources


def load_web_service_client_config(purpose):
    config = load_config_from(VEIL_ETC_DIR / '{}-web-service.cfg'.format(purpose.replace('_', '-')),
        'url')
    return config