from __future__ import unicode_literals, print_function, division
from veil.utility.path import *
from veil.frontend.template import *
from veil.environment.setting import *
from veil.environment.installation import *

@installation_script()
def install_redis_server(purpose=None):
    if not purpose:
        return
    settings = get_settings()
    config = getattr(settings, '{}_redis'.format(purpose))
    install_ubuntu_package('redis-server')
    remove_service_auto_start('redis-server', '/etc/rc0.d/K20redis-server')
    redis_dbdir = as_path(config.dbdir)
    create_directory(redis_dbdir, owner=config.owner, group=config.owner_group, mode=0770)
    redis_configfile = as_path(config.configfile)
    create_file(redis_configfile, content=get_template('redis.conf.j2').render(config=config))
