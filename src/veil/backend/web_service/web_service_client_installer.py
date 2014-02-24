from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

@composite_installer
def web_service_client_resource(purpose, url, user, password, proxy_netloc):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(path=VEIL_ETC_DIR / '{}-web-service.cfg'.format(purpose.replace('_', '-')),
        content=render_config('web-service-client.cfg.j2', url=url, user=user, password=password, proxy_netloc=proxy_netloc)))
    return resources


def load_web_service_client_config(purpose):
    config = load_config_from(VEIL_ETC_DIR / '{}-web-service.cfg'.format(purpose.replace('_', '-')), 'url', 'user', 'password', 'proxy_netloc')
    return config