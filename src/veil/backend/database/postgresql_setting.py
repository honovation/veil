from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


def postgresql_program(purpose, version, host, port, owner, owner_password, user, password, log_min_duration_statement, log_filename=None,
                       shared_buffers='24MB', work_mem='1MB', maintenance_work_mem='16MB', effective_io_concurrency=1, checkpoint_completion_target=0.5,
                       effective_cache_size='128MB', enable_chinese_fts=False, replication_user=None, replication_host=None, checkpoint_timeout=None,
                       bgwriter_delay=None, bgwriter_lru_maxpages=None, vacuum_cost_limit=None, autovacuum_vacuum_cost_delay=None, autovacuum_max_workers=None):
    return objectify({
        '{}_postgresql'.format(purpose): {
            'execute_command': '{}/postgres -D {}'.format(get_pg_bin_dir(version), get_pg_data_dir(purpose, version)),
            'migrate_command': 'veil backend database postgresql migrate {}'.format(purpose),
            'priority': 100,
            'stopsignal': 'INT',  # use the "fast" shutdown signal SIGINT
            'stopwaitsecs': 60,
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
                    'checkpoint_completion_target': checkpoint_completion_target,
                    'effective_cache_size': effective_cache_size,
                    'log_min_duration_statement': log_min_duration_statement,
                    'log_filename': log_filename,  # set to None, postgresql will rotate it for us
                    'enable_chinese_fts': enable_chinese_fts,
                    'replication_user': replication_user,
                    'replication_host': replication_host
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


def barman_periodic_backup_program(crontab_expression, purpose):
    return objectify({
        'barman_backup': {
            'execute_command': 'veil backend database postgresql barman-backup "{}" {}'.format(crontab_expression, purpose)
        }
    })


def barman_periodic_recover_program(crontab_expression, purpose, host, port, user):
    return objectify({
        'barman_recover': {
            'execute_command': 'veil backend database postgresql barman-recover "{}" {} {} {} {}'.format(crontab_expression, purpose, host, port, user)
        }
    })
