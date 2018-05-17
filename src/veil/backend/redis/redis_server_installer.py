from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

REDIS_SERVER_SOURCE_CODE_VERSION = '4.0.9'


@composite_installer
def redis_server_resource(purpose, host, port, persisted_by_aof=False, snapshot_configs=None):
    data_directory = VEIL_DATA_DIR / '{}-redis'.format(purpose.replace('_', '-'))
    redis_config = DictObject({'host': host, 'port': port, 'data_directory': data_directory, 'persisted_by_aof': persisted_by_aof,
                               'snapshot_configs': snapshot_configs or ()})
    if redis_config.snapshot_configs:
        redis_config.dump_file = '{}-backup.rdb'.format(purpose)
    return [
        os_ppa_repository_resource(name='chris-lea/redis-server'), # for latest redis-server
        os_package_resource(name='redis-server'),
        os_service_auto_starting_resource(name='redis-server', state='not_installed'),
        directory_resource(path=data_directory, owner=CURRENT_USER, group=CURRENT_USER_GROUP, mode=0770),
        file_resource(path=VEIL_ETC_DIR / '{}-redis.conf'.format(purpose.replace('_', '-')), content=render_config('redis-server.conf.j2', config=redis_config))
    ]


@composite_installer
def redis_server_source_code_resource(purpose, host, port, persisted_by_aof=False, snapshot_configs=None):
    data_directory = VEIL_DATA_DIR / '{}-redis'.format(purpose.replace('_', '-'))
    redis_config = DictObject({'host': host, 'port': port, 'data_directory': data_directory, 'persisted_by_aof': persisted_by_aof,
                               'snapshot_configs': snapshot_configs or ()})
    if redis_config.snapshot_configs:
        redis_config.dump_file = '{}-backup.rdb'.format(purpose)

    return [
        redis_server_os_source_code_resource(version=REDIS_SERVER_SOURCE_CODE_VERSION),
        directory_resource(path=data_directory, owner=CURRENT_USER, group=CURRENT_USER_GROUP, mode=0770),
        file_resource(path=VEIL_ETC_DIR / '{}-redis.conf'.format(purpose.replace('_', '-')), content=render_config('redis-server.conf.j2', config=redis_config),
                      owner=CURRENT_USER, group=CURRENT_USER_GROUP)
    ]


@atomic_installer
def redis_server_os_source_code_resource(version):
    installed_file_name = '.installed'
    tgz_name = 'redis-{}.tar.gz'.format(version)
    local_path = DEPENDENCY_DIR / tgz_name
    if not local_path.exists():
        shell_execute('wget -c http://download.redis.io/releases/{} -O {}'.format(tgz_name, local_path))
    redis_source_code_path = DEPENDENCY_INSTALL_DIR / 'redis-{}'.format(version)
    if not redis_source_code_path.exists():
        shell_execute('tar zxvf {} -C {}'.format(tgz_name, DEPENDENCY_INSTALL_DIR), cwd=DEPENDENCY_DIR)
    installed_path = redis_source_code_path / installed_file_name
    if installed_path.exists():
        return
    shell_execute('make', cwd=redis_source_code_path)
    shell_execute('sudo make install', cwd=redis_source_code_path)
    shell_execute('touch {}'.format(installed_file_name), cwd=redis_source_code_path)
