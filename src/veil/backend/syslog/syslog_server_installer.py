from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment import *

@composite_installer
def syslog_server_resource():
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(os_package_resource(name='syslog-ng'))
    resources.append(os_service_resource(state='not_installed', name='syslog-ng', path='/etc/rc0.d/K90syslog-ng'))
    resources.append(file_resource(path=VEIL_ETC_DIR / 'syslog-ng.conf', content=render_config(
        'syslog-ng.conf.j2')))
    return resources