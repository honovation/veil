from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from veil.frontend.template import *
from veil.environment import *
from veil.environment.setting import *
from veil.backend.shell import *
from veil_installer import *


@composite_installer('redis')
@using_isolated_template
def install_redis_server(name):
    purpose = name
    settings = get_settings()
    config = getattr(settings, '{}_redis'.format(purpose))
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        os_package_resource('redis-server'),
        os_service_resource(state='not_installed', name='redis-server', path='/etc/rc0.d/K20redis-server'),
        directory_resource(config.dbdir, owner=config.owner, group=config.owner_group, mode=0770),
        file_resource(config.configfile, content=get_template('redis.conf.j2').render(config=config))
    ])
    return [], resources


@script('server-up')
def bring_up_redis_server(purpose):
    settings = get_settings()
    config = getattr(settings, '{}_redis'.format(purpose))
    pass_control_to('redis-server {}'.format(config.configfile))