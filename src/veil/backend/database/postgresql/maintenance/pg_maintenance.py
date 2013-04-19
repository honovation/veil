from __future__ import unicode_literals, print_function, division
import logging
import sys
import time
import os
import hashlib
from veil.utility.shell import *
from veil.frontend.cli import *
from veil.environment import *
from veil.server.supervisor import *
from veil.utility.clock import *
from veil_component import *
from veil.backend.database.client import *
from ..server.pg_server_installer import load_postgresql_maintenance_config

LOGGER = logging.getLogger(__name__)

@script('drop-database')
def drop_database(purpose):
    if VEIL_SERVER not in ['development', 'test']:
        raise Exception('not allow to drop database other than development or test')
    if 'development' == VEIL_SERVER:
        supervisorctl('restart', '{}_postgresql'.format(purpose))
        wait_for_server_up(purpose)
    try:
        config = load_database_client_config(purpose)
        maintenance_config = load_postgresql_maintenance_config(purpose)
        env = os.environ.copy()
        env['PGPASSWORD'] = maintenance_config.owner_password
        shell_execute('dropdb -h {host} -p {port} -U {owner} {database}'.format(
            host=config.host,
            port=config.port,
            owner=maintenance_config.owner,
            database=config.database), env=env, capture=True)
    except ShellExecutionError, e:
        if 'not exist' in e.output:
            pass # ignore
        else:
            raise

@script('migrate')
def migrate(purpose):
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
        max_version = max(versions.keys()) if versions else None
        if from_version > max_version:
            LOGGER.info('[MIGRATE] postgresql server current version higher than code: %(purpose)s is version %(from_version)s, code is version %(max_version)s', {
                'purpose': purpose,
                'from_version': from_version,
                'max_version': max_version
            })
            sys.exit(1)
        if from_version == max_version:
            LOGGER.info('[MIGRATE] postgresql server is up to date: %(purpose)s is version %(from_version)s', {
                'purpose': purpose,
                'from_version': from_version
            })
            sys.exit(0)
        LOGGER.info(
            '[MIGRATE] about to migrate postgresql server: %(purpose)s from %(from_version)s to %(max_version)s', {
                'purpose': purpose,
                'from_version': from_version,
                'max_version': max_version
            })
        to_version = None
        for i in range(current_version, max_version):
            to_version = i + 1
            LOGGER.info('[MIGRATE] upgrading one version: from %(from_version)s to %(to_version)s ...', {
                'from_version': to_version - 1,
                'to_version': to_version
            })
            db().execute(versions[to_version].text('utf8'))
        db().insert(
            'database_migration_event', from_version=from_version,
            to_version=to_version, migrated_at=get_current_time())
        LOGGER.info('[MIGRATE] migrated postgresql server: %(purpose)s from %(from_version)s to %(max_version)s', {
            'purpose': purpose,
            'from_version': from_version,
            'max_version': max_version
        })

    execute_migration_scripts()


def wait_for_server_up(purpose):
    for i in range(20):
        try:
            psql(purpose, '-c "SELECT 1"', database='postgres', capture=True)
            break
        except:
            import traceback
            traceback.print_exc()
            LOGGER.info('[MIGRATE] wait for postgresql...')
            time.sleep(3)


@script('create-database')
def create_database_if_not_exists(purpose):
    try:
        config = load_database_client_config(purpose)
        maintenance_config = load_postgresql_maintenance_config(purpose)
        env = os.environ.copy()
        env['PGPASSWORD'] = maintenance_config.owner_password
        shell_execute('createdb -h {host} -p {port} -U {owner} {database} -E {encoding}'.format(
            host=config.host,
            port=config.port,
            owner=maintenance_config.owner,
            database=config.database,
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
    config = load_database_client_config(purpose)
    env = os.environ.copy()
    env['PGPASSWORD'] = config.password
    shell_execute('psql -h {host} -p {port} -U {user} {extra_arg} --set ON_ERROR_STOP=1 {database}'.format(
        host=config.host,
        port=config.port,
        user=config.user,
        database=database or config.database,
        extra_arg=extra_arg), env=env, **kwargs)


@script('lock-migration-scripts')
def lock_migration_scripts(purpose):
    migration_script_dir = VEIL_HOME / 'db' / purpose
    for sql_path in migration_script_dir.listdir('*.sql'):
        with open(sql_path) as sql_file:
            md5 = calculate_file_md5_hash(sql_file)
        lock_path = as_path(sql_path.replace('.sql', '.locked'))
        lock_path.write_text(md5)

def calculate_file_md5_hash(file_object, reset_position=False, hex=True):
    """ Calculate the md5 hash for this file.

    This reads through the entire file.
    """
    assert file_object is not None and file_object.tell() == 0
    try:
        m = hashlib.md5()
        for chunk in iter_file_in_chunks(file_object):
            m.update(chunk)
        return m.hexdigest() if hex else m.digest()
    finally:
        if reset_position:
            file_object.seek(0)


def iter_file_in_chunks(file_object, chunk_size=8192):
    """Lazy function (generator) to read a file piece by piece.
    Default chunk size: 8k."""
    return iter(lambda: file_object.read(chunk_size), b'')

@script('reset')
def reset(purpose):
    shell_execute('veil backend database postgresql drop-database {}'.format(purpose))
    shell_execute('veil backend database postgresql migrate {}'.format(purpose))

def check_if_locked_migration_scripts_being_changed():
    if not os.path.exists(VEIL_HOME / 'db'):
        return
    for purpose in os.listdir(VEIL_HOME / 'db'):
        file_names = set(os.listdir(VEIL_HOME / 'db' / purpose))
        for sql_file_name in file_names:
            locked_file_name = sql_file_name.replace('.sql', '.locked')
            if sql_file_name.endswith('.sql') and locked_file_name in file_names:
                expected_md5 = open(VEIL_HOME / 'db' / purpose / locked_file_name).read()
                sql_path = VEIL_HOME / 'db' / purpose / sql_file_name
                with open(sql_path) as f:
                    actual_md5 = calculate_file_md5_hash(f)
                if actual_md5 != expected_md5:
                    raise Exception('locked migration script {} should not be changed'.format(sql_path))


def check_all_locked_migration_scripts():
    if not os.path.exists(VEIL_HOME / 'db'):
        return
    migration_script_dir = VEIL_HOME / 'db'
    purposes = migration_script_dir.listdir()
    for purpose in purposes:
        locked_file_count = len(purpose.listdir('*.locked'))
        script_file_count = len(purpose.listdir('*.sql'))
        if locked_file_count < script_file_count:
            print('You must lock scripts in {} using: veil backend database postgresql lock-migration-scripts {}'.format(purpose, purpose))
            exit(-1)
        else:
            print('Migration script check in {} ...passed!'.format(purpose))