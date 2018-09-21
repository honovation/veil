from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


def postgresql_program(purpose, version, host, port, owner, owner_password, user, password, log_min_duration_statement,
                       log_filename=None, enable_chinese_fts=False, replication_user=None, barman_host=None, replication_hosts=(), **more_config):
    config = {
        'purpose': purpose,
        'version': version,
        'host': host,
        'port': port,
        'owner': owner,
        'owner_password': owner_password,
        'user': user,
        'password': password,

        'log_destination': 'csvlog',
        'logging_collector': True,
        'log_checkpoints': True,
        'log_connections': True,
        'log_disconnections': True,
        'log_duration': False,
        'log_min_duration_statement': log_min_duration_statement,
        'log_filename': log_filename,  # set to None, postgresql will rotate it for us

        'enable_chinese_fts': enable_chinese_fts,

        'replication_user': replication_user,
        'barman_host': barman_host,
        'replication_hosts': replication_hosts
    }
    config.update(more_config)
    return objectify({
        '{}_postgresql'.format(purpose): {
            'execute_command': '{}/postgres -D {}'.format(get_pg_bin_dir(version), get_pg_data_dir(purpose, version)),
            'migrate_command': 'veil backend database postgresql migrate {}'.format(purpose),
            'priority': 100,
            'stopsignal': 'INT',  # use the "fast" shutdown signal SIGINT
            'stopwaitsecs': 60,
            'resources': [('veil.backend.database.postgresql.postgresql_server_resource', {'config': config})]
        },
        'pg_routines'.format(purpose): {
            'execute_command': 'veil backend database postgresql routines-up {}'.format(purpose),
            'resources': [('veil_installer.component_resource', {
                'name': 'veil.backend.database.postgresql'
            })]
        }
    })


def get_pg_config_dir(purpose, version=None):
    return VEIL_ETC_DIR / '{}-postgresql{}'.format(purpose.replace('_', '-'), '-{}'.format(version) if version else '')


def get_pg_data_dir(purpose, version):
    return VEIL_DATA_DIR / '{}-postgresql-{}'.format(purpose.replace('_', '-'), version)


def get_pg_bin_dir(version):
    return as_path('/usr/lib/postgresql/{}/bin'.format(version))


def get_pg_lib_dir(version):
    return as_path('/usr/lib/postgresql/{}/lib'.format(version))


def get_pg_tsearch_data_dir(version):
    return as_path('/usr/share/postgresql/{}/tsearch_data'.format(version))
