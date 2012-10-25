from __future__ import unicode_literals, print_function, division
import logging
from veil.environment.setting import *
from veil.backend.shell import *
from veil.frontend.cli import *
from veil.environment import *
from veil.supervisor import *
from veil.utility.clock import *
from veil.backend.database.client import *
import sys

LOGGER = logging.getLogger(__name__)

@script('create-database')
def create_database(purpose):
    try:
        env = os.environ.copy()
        env['PGPASSWORD'] = get_option(purpose, 'owner_password')
        shell_execute('createdb -h {host} -p {port} -U {owner} {database}'.format(
            host=get_option(purpose, 'host'),
            port=get_option(purpose, 'port'),
            owner=get_option(purpose, 'owner'),
            database=get_option(purpose, 'database')), env=env, capture=True)
        db = register_database(purpose)
        db().execute(
            """
            CREATE TABLE IF NOT EXISTS database_migration_event (
                id SERIAL PRIMARY KEY,
                from_version INT NOT NULL,
                to_version INT NOT NULL,
                migrated_at TIMESTAMP WITH TIME ZONE NOT NULL
            )
            """)
    except ShellExecutionError, e:
        if 'already exists' in e.output:
            pass # ignore
        else:
            raise


@script('drop-database')
def drop_database(purpose):
    supervisorctl('restart', '{}_postgresql'.format(purpose))
    try:
        env = os.environ.copy()
        env['PGPASSWORD'] = get_option(purpose, 'owner_password')
        shell_execute('dropdb -h {host} -p {port} -U {owner} {database}'.format(
            host=get_option(purpose, 'host'),
            port=get_option(purpose, 'port'),
            owner=get_option(purpose, 'owner'),
            database=get_option(purpose, 'database')), env=env, capture=True)
    except ShellExecutionError, e:
        if 'not exist' in e.output:
            pass # ignore
        else:
            raise


@script('migrate')
def migrate(purpose):
    versions = load_versions(purpose)
    db = register_database(purpose)

    @transactional(db)
    def execute_migration_scripts():
        current_version = db().get_scalar(
            """
            SELECT to_version
            FROM database_migration_event
            ORDER BY id DESC
            LIMIT 1
            """) or 0
        from_version = current_version
        max_version = max(versions.keys())
        if from_version > max_version:
            print('[MIGRATION] current version {} is higher than the code {}'.format(from_version, max_version))
            sys.exit(1)
        if from_version == max_version:
            print('[MIGRATION] current version {} is up to date'.format(from_version))
            sys.exit(0)
        print('[MIGRATION] about to migrate postgresql server {} from {} to {}'.format(purpose, from_version, max_version))
        to_version = None
        for i in range(current_version, max_version):
            to_version = i + 1
            print('[MIGRATION] migrating from {} to {} ...'.format(to_version - 1, to_version))
            db().execute(versions[to_version].text('utf8'))
        db().insert(
            'database_migration_event', from_version=from_version,
            to_version=to_version, migrated_at=get_current_time())
        print('[MIGRATION] migrated postgresql server {} from {} to {}'.format(purpose, from_version, max_version))

    execute_migration_scripts()


def load_versions(purpose):
    migration_script_dir = VEIL_HOME / 'db' / purpose
    versions = {}
    for migration_script in migration_script_dir.listdir('*.sql'):
        _, file_name = migration_script.splitpath()
        if '-' not in file_name:
            raise Exception('invalid migration script name: {}'.format(file_name))
        version = int(file_name.split('-')[0])
        if version in versions:
            raise Exception('{} duplicated with {}'.format(file_name, versions[version]))
        versions[version] = migration_script
    return versions


def execute_migration_script(purpose, migration_script):
    env = os.environ.copy()
    env['PGPASSWORD'] = get_option(purpose, 'owner_password')
    shell_execute('psql -h {host} -p {port} -U {user} -f {migration_script} --set ON_ERROR_STOP=1 {database}'.format(
        host=get_option(purpose, 'host'),
        port=get_option(purpose, 'port'),
        user=get_option(purpose, 'user'),
        database=get_option(purpose, 'database'),
        migration_script=migration_script), env=env)


@script('reset')
def reset(purpose):
    shell_execute('veil backend database postgresql drop-database {}'.format(purpose))
    shell_execute('veil backend database postgresql create-database {}'.format(purpose))
    shell_execute('veil backend database postgresql migrate {}'.format(purpose))


def get_option(purpose, key):
    return get_settings()['{}_postgresql'.format(purpose)][key]
