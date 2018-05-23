from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


@composite_installer
def redis_server_resource(purpose, host, port, persisted_by_aof=False, snapshot_configs=None):
    data_directory = VEIL_DATA_DIR / '{}-redis'.format(purpose.replace('_', '-'))
    redis_config = DictObject({'host': host, 'port': port, 'data_directory': data_directory, 'persisted_by_aof': persisted_by_aof,
                               'snapshot_configs': snapshot_configs or ()})
    if redis_config.snapshot_configs:
        redis_config.dump_file = '{}-backup.rdb'.format(purpose)
    return [
        os_ppa_repository_resource(name='chris-lea/redis-server'), # for latest redis-server
        os_package_resource(name='redis-server', cmd_run_before_install='sudo systemctl mask redis-server.service'),
        os_service_auto_starting_resource(name='redis-server', state='not_installed'),
        directory_resource(path=data_directory, owner=CURRENT_USER, group=CURRENT_USER_GROUP, mode=0770),
        file_resource(path=VEIL_ETC_DIR / '{}-redis.conf'.format(purpose.replace('_', '-')), content=render_config('redis-server.conf.j2', config=redis_config))
    ]
