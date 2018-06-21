from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


@composite_installer
def redis_server_resource(purpose, host, port, max_memory=None, max_memory_policy=None, enable_aof=False, aof_fsync=None, enable_snapshot=True,
                          snapshot_configs=()):
    data_directory = VEIL_DATA_DIR / '{}-redis'.format(purpose.replace('_', '-'))
    redis_config = DictObject(
        {'purpose': purpose, 'host': host, 'port': port, 'max_memory': max_memory, 'max_memory_policy': max_memory_policy, 'enable_aof': enable_aof,
         'aof_fsync': aof_fsync, 'enable_snapshot': enable_snapshot, 'snapshot_configs': snapshot_configs, 'data_directory': data_directory})
    return [
        os_package_resource(name='redis-server', cmd_run_before_install='sudo systemctl mask redis-server.service'),
        os_service_auto_starting_resource(name='redis-server', state='not_installed'),
        directory_resource(path=data_directory, owner=CURRENT_USER, group=CURRENT_USER_GROUP, mode=0770, recursive=True),
        file_resource(path=VEIL_ETC_DIR / '{}-redis.conf'.format(purpose.replace('_', '-')), content=render_config('redis-server.conf.j2', config=redis_config),
                      owner=CURRENT_USER, group=CURRENT_USER_GROUP)
    ]
