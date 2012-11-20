from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.frontend.template import *
from veil.environment import *
from veil.environment.setting import *

@composite_installer('web_service_client')
@using_isolated_template
def install_web_service_client(purpose, url):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(
        file_resource(VEIL_ETC_DIR / '{}-web-service.cfg'.format(purpose.replace('_', '-')), content=get_template(
            'web-service-client.cfg.j2').render(url=url)))
    return [], resources


def load_web_service_client_config(purpose):
    config = load_config_from(VEIL_ETC_DIR / '{}-web-service.cfg'.format(purpose.replace('_', '-')),
        'url')
    return config