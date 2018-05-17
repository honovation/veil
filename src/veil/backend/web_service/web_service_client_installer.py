from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

_config = {}


@composite_installer
def web_service_resource(purpose, url, user, password, proxy_netloc):
    return [
        file_resource(path=VEIL_ETC_DIR / '{}-web-service.cfg'.format(purpose.replace('_', '-')),
                      content=render_config('web-service.cfg.j2', url=url, user=user, password=password, proxy_netloc=proxy_netloc),
                      owner=CURRENT_USER, group=CURRENT_USER_GROUP)
    ]


def load_web_service_config(purpose):
    return load_config_from(VEIL_ETC_DIR / '{}-web-service.cfg'.format(purpose.replace('_', '-')), 'url', 'user', 'password', 'proxy_netloc')


def web_service_config(purpose):
    return _config.setdefault(purpose, load_web_service_config(purpose))
