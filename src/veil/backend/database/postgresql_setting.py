from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


def postgresql_program(purpose, version, host, port, owner, owner_password, user, password, log_min_duration_statement, log_filename=None,
                       enable_chinese_fts=False, replication_user=None, replication_host=None, **more_config):
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
        'replication_host': replication_host
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
