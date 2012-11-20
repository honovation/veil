from __future__ import unicode_literals, print_function, division
from veil.frontend.template import *
from veil.environment import *
from veil_installer import *


@composite_installer('redis_server')
@using_isolated_template
def install_redis_server(purpose, host, port):
    resources = list(BASIC_LAYOUT_RESOURCES)
    data_directory = VEIL_VAR_DIR / '{}-redis'.format(purpose.replace('_', '-'))
    resources.extend([
        os_package_resource('redis-server'),
        os_service_resource(state='not_installed', name='redis-server', path='/etc/rc0.d/K20redis-server'),
        directory_resource(
            data_directory,
            owner=CURRENT_USER, group=CURRENT_USER_GROUP, mode=0770),
        file_resource(
            VEIL_ETC_DIR / '{}-redis.conf'.format(purpose.replace('_', '-')),
            content=get_template('redis-server.conf.j2').render(config={
                'host': host,
                'port': port,
                'data_directory': data_directory
            }))
    ])
    return [], resources