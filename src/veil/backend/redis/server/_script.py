from __future__ import unicode_literals, print_function, division
from veil.frontend.script import *
from veil.backend.path import *
from veil.frontend.template import *
from veil.environment.deployment import *

@script('install')
def install_redis_server():
    settings = get_deployment_settings()
    install_ubuntu_package('redis-server')
    remove_service_auto_start('redis-server', '/etc/rc0.d/K20redis-server')
    redis_owner = settings.redis.owner
    assert redis_owner, 'must specify redis owner'
    redis_group = getattr(settings.redis, 'group', None) or redis_owner
    redis_dbdir = settings.redis.dbdir
    assert redis_dbdir, 'must specify redis database directory'
    redis_dbdir = path(redis_dbdir)
    create_directory(redis_dbdir, owner=redis_owner, group=redis_group, mode=0770)
    redis_configfile = settings.redis.configfile
    assert redis_configfile, 'must specify redis configuration file'
    redis_configfile = path(redis_configfile)
    create_file(redis_configfile, content=get_template('redis.conf.j2').render(config=settings.redis))