from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


def postgresql_program(purpose, version, host, port, owner, owner_password, user, password, log_min_duration_statement, log_filename=None,
        shared_buffers='24MB', work_mem='1MB', maintenance_work_mem='16MB', effective_io_concurrency=1, checkpoint_segments=3,
        checkpoint_completion_target=0.5, effective_cache_size='128MB', kernel_shmmax=None, kernel_shmall=None, enable_zhparser=False):
    return objectify({
        '{}_postgresql'.format(purpose): {
            'execute_command': '{}/postgres -D {}'.format(get_pg_bin_dir(version), get_pg_data_dir(purpose, version)),
            'migrate_command': 'veil backend database postgresql migrate {}'.format(purpose),
            'priority': 100,
            'stop_signal': 'INT', # use the "fast" shutdown signal SIGINT
            'stopwaitsecs': 20,
            'resources': [('veil.backend.database.postgresql.postgresql_server_resource', {
                'purpose': purpose,
                'config': {
                    'version': version,
                    'host': host,
                    'port': port,
                    'owner': owner,
                    'owner_password': owner_password,
                    'user': user,
                    'password': password,
                    'shared_buffers': shared_buffers,
                    'work_mem': work_mem,
                    'maintenance_work_mem': maintenance_work_mem,
                    'effective_io_concurrency': effective_io_concurrency,
                    'checkpoint_segments': checkpoint_segments,
                    'checkpoint_completion_target': checkpoint_completion_target,
                    'effective_cache_size': effective_cache_size,
                    'kernel_shmmax': kernel_shmmax,
                    'kernel_shmall': kernel_shmall,
                    'log_min_duration_statement': log_min_duration_statement,
                    'log_filename': log_filename, # set to None, postgresql will rotate it for us
                    'enable_zhparser': enable_zhparser
                }
            })]
        }
    })


def get_pg_config_dir(purpose, version=None):
    return VEIL_ETC_DIR / '{}-postgresql{}'.format(purpose.replace('_', '-'), '-{}'.format(version) if version else '')


def get_pg_data_dir(purpose, version):
    return VEIL_DATA_DIR / '{}-postgresql-{}'.format(purpose.replace('_', '-'), version)


def get_pg_bin_dir(version):
    return as_path('/usr/lib/postgresql/{}/bin'.format(version))
