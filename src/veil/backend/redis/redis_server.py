from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from veil.frontend.template import *
from veil.environment import *
from veil.environment.setting import *
from veil.utility.shell import *
from veil_installer import *


@composite_installer('redis')
@using_isolated_template
def install_redis_server(purpose, host, port):
    resources = list(BASIC_LAYOUT_RESOURCES)
    data_directory = VEIL_VAR_DIR / '{}_redis'.format(purpose)
    resources.extend([
        os_package_resource('redis-server'),
        os_service_resource(state='not_installed', name='redis-server', path='/etc/rc0.d/K20redis-server'),
        directory_resource(
            data_directory,
            owner=CURRENT_USER, group=CURRENT_USER_GROUP, mode=0770),
        file_resource(
            VEIL_ETC_DIR / '{}_redis.conf'.format(purpose),
            content=get_template('redis.conf.j2').render(config={
                'host': host,
                'port': port,
                'data_directory': data_directory
            }))
    ])
    return [], resources


@script('server-up')
def bring_up_redis_server(purpose):
    settings = get_settings()
    config = getattr(settings, '{}_redis'.format(purpose))
    pass_control_to('redis-server {}'.format(config.configfile))