from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.environment import *

def postgresql_program(purpose, version, host, port, owner, owner_password, user, password, log_min_duration_statement, log_filename=None,
        shared_buffers='24MB', work_mem='1MB', maintenance_work_mem='16MB', effective_io_concurrency=1, wal_buffers='64kB', checkpoint_segments=3,
        checkpoint_completion_target=0.5, effective_cache_size='128MB'):
    data_dir = VEIL_VAR_DIR / '{}-postgresql'.format(purpose.replace('_', '-'))
    return objectify({
        '{}_postgresql'.format(purpose): {
            'execute_command': 'postgres -D {}'.format(data_dir),
            'migrate_command': 'veil backend database postgresql migrate {}'.format(purpose),
            'resources': [('veil.backend.database.postgresql.postgresql_server_resource', {
                'purpose': purpose,
                'version': version,
                'config': {
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
                    'wal_buffers': wal_buffers,
                    'checkpoint_segments': checkpoint_segments,
                    'checkpoint_completion_target': checkpoint_completion_target,
                    'effective_cache_size': effective_cache_size,
                    'log_min_duration_statement': log_min_duration_statement,
                    'log_filename': log_filename # set to None, postgresql will rotate it for us
                }
            })]
        }
    })