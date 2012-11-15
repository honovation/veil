from __future__ import unicode_literals, print_function, division
import logging
import sys
import time
import os
from veil.environment.setting import *
from veil.utility.shell import *
from veil.frontend.cli import *
from veil.environment import *
from veil.environment.supervisor import *
from veil.utility.clock import *
from veil.utility.hash import *
from veil.utility.path import *
from veil.backend.database.client import *

LOGGER = logging.getLogger(__name__)

@script('drop-database')
def drop_database(purpose):
    if VEIL_SERVER not in ['development', 'test']:
        raise Exception('not allow to drop database other than development or test')
    if 'development' == VEIL_SERVER:
        supervisorctl('restart', '{}_postgresql'.format(purpose))
        wait_for_server_up(purpose)
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


@script('migrate-all')
def migrate_all():
    for key in get_settings().keys():
        if key.endswith('_postgresql'):
            purpose = key.replace('_postgresql', '')
            try:
                migrate(purpose)
            except SystemExit:
                pass


@script('migrate')
def migrate(purpose):
    if not is_current_veil_server_hosting('{}_postgresql'.format(purpose)):
        print('[MIGRATE] skip {}, as not hosted by this server'.format(purpose))
        return
    wait_for_server_up(purpose)
    create_database_if_not_exists(purpose)
    versions = load_versions(purpose)
    db = lambda: require_database(purpose)

    @transactional(db)
    def execute_migration_scripts():
        create_database_migration_table_if_not_exists(purpose)
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
            print('[MIGRATE] postgresql server {} current version {} is higher than the code {}'.format(
                purpose, from_version, max_version))
            sys.exit(1)
        if from_version == max_version:
            print('[MIGRATE] postgresql server {} current version {} is up to date'.format(purpose, from_version))
            sys.exit(0)
        print(
            '[MIGRATE] about to migrate postgresql server {} from {} to {}'.format(purpose, from_version, max_version))
        to_version = None
        for i in range(current_version, max_version):
            to_version = i + 1
            print('[MIGRATE] migrating from {} to {} ...'.format(to_version - 1, to_version))
            db().execute(versions[to_version].text('utf8'))
        db().insert(
            'database_migration_event', from_version=from_version,
            to_version=to_version, migrated_at=get_current_time())
        print('[MIGRATE] migrated postgresql server {} from {} to {}'.format(purpose, from_version, max_version))

    execute_migration_scripts()


def wait_for_server_up(purpose):
    for i in range(20):
        try:
            psql(purpose, '-c "SELECT 1"', database='postgres', capture=True)
            break
        except:
            print('[MIGRATE] wait for postgresql...')
            time.sleep(3)


def create_database_if_not_exists(purpose):
    try:
        env = os.environ.copy()
        env['PGPASSWORD'] = get_option(purpose, 'owner_password')
        shell_execute('createdb -h {host} -p {port} -U {owner} {database} -E {encoding}'.format(
            host=get_option(purpose, 'host'),
            port=get_option(purpose, 'port'),
            owner=get_option(purpose, 'owner'),
            database=get_option(purpose, 'database'),
            encoding='UTF8'), env=env, capture=True)
    except ShellExecutionError, e:
        if 'already exists' in e.output:
            pass # ignore
        else:
            raise


def create_database_migration_table_if_not_exists(purpose):
    db = lambda: require_database(purpose)
    db().execute(
        """
        CREATE TABLE IF NOT EXISTS database_migration_event (
            id SERIAL PRIMARY KEY,
            from_version INT NOT NULL,
            to_version INT NOT NULL,
            migrated_at TIMESTAMP WITH TIME ZONE NOT NULL
        )
        """)


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
    psql(purpose, '-f {}'.format(migration_script))


def psql(purpose, extra_arg, database=None, **kwargs):
    env = os.environ.copy()
    env['PGPASSWORD'] = get_option(purpose, 'owner_password')
    shell_execute('psql -h {host} -p {port} -U {user} {extra_arg} --set ON_ERROR_STOP=1 {database}'.format(
        host=get_option(purpose, 'host'),
        port=get_option(purpose, 'port'),
        user=get_option(purpose, 'user'),
        database=database or get_option(purpose, 'database'),
        extra_arg=extra_arg), env=env, **kwargs)


@script('lock-migration-scripts')
def lock_migration_scripts(purpose):
    migration_script_dir = VEIL_HOME / 'db' / purpose
    for sql_path in migration_script_dir.listdir('*.sql'):
        with open(sql_path) as sql_file:
            md5 = calculate_file_md5_hash(sql_file)
        lock_path = as_path(sql_path.replace('.sql', '.locked'))
        lock_path.write_text(md5)


@script('reset-all')
def reset_all():
    for key in get_settings().keys():
        if key.endswith('_postgresql'):
            purpose = key.replace('_postgresql', '')
            reset(purpose)


@script('reset')
def reset(purpose):
    shell_execute('veil backend database postgresql drop-database {}'.format(purpose))
    shell_execute('veil backend database postgresql migrate {}'.format(purpose))


def get_option(purpose, key):
    return get_settings()['{}_postgresql'.format(purpose)][key]


def check_if_locked_migration_scripts_being_changed():
    for purpose in os.listdir('./db'):
        file_names = set(os.listdir('./db/{}'.format(purpose)))
        for sql_file_name in file_names:
            locked_file_name = sql_file_name.replace('.sql', '.locked')
            if sql_file_name.endswith('.sql') and locked_file_name in file_names:
                expected_md5 = open('./db/{}/{}'.format(purpose, locked_file_name)).read()
                sql_path = './db/{}/{}'.format(purpose, sql_file_name)
                with open(sql_path) as f:
                    actual_md5 = calculate_file_md5_hash(f)
                if actual_md5 != expected_md5:
                    raise Exception('locked migration script {} should not be changed'.format(sql_path))