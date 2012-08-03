from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from sandal.path import *
from veil.frontend.template import *
from veil.environment.deployment import *
from veil.backend.shell import *

@script('install')
def install_redis_server(purpose='redis'):
    settings = get_deployment_settings()
    config = getattr(settings, purpose)
    install_ubuntu_package('redis-server')
    remove_service_auto_start('redis-server', '/etc/rc0.d/K20redis-server')
    redis_dbdir = path(config.dbdir)
    create_directory(redis_dbdir, owner=config.owner, group=config.owner_group, mode=0770)
    redis_configfile = path(config.configfile)
    create_file(redis_configfile, content=get_template('redis.conf.j2').render(config=config))


@script('up')
def bring_up_redis_server(purpose='redis'):
    settings = get_deployment_settings()
    config = getattr(settings, purpose)
    pass_control_to('redis-server {}'.format(config.configfile))