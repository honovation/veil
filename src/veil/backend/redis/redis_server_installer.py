from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


@composite_installer
def redis_server_resource(purpose, host, port, persisted_by_aof=False):
    resources = list(BASIC_LAYOUT_RESOURCES)
    data_directory = VEIL_VAR_DIR / '{}-redis'.format(purpose.replace('_', '-'))
    resources.extend([
        os_ppa_repository_resource(name='rwky/redis'), # for latest redis-server
        os_package_resource(name='redis-server'),
        os_service_resource(state='not_installed', name='redis-server'),
        directory_resource(path=data_directory, owner=CURRENT_USER, group=CURRENT_USER_GROUP, mode=0770),
        file_resource(
            path=VEIL_ETC_DIR / '{}-redis.conf'.format(purpose.replace('_', '-')),
            content=render_config('redis-server.conf.j2', config={
                'host': host,
                'port': port,
                'data_directory': data_directory,
                'persisted_by_aof': persisted_by_aof
            }))
    ])
    return resources