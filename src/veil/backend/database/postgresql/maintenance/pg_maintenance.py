from __future__ import unicode_literals, print_function, division
import logging
import sys
import time
import os
from veil_component import VEIL_ENV
from veil.utility.clock import *
from veil.utility.shell import *
from veil.frontend.cli import *
from veil.server.supervisor import *
from veil.backend.database.migration import *
from veil.backend.database.client import *
from ...postgresql_setting import get_pg_bin_dir
from ..server.pg_server_installer import postgresql_maintenance_config

LOGGER = logging.getLogger(__name__)


@script('drop-database')
def drop_database(purpose):
    if not (VEIL_ENV.is_dev or VEIL_ENV.is_test):
        raise Exception('not allow to drop database other than development or test')
    if VEIL_ENV.is_dev:
        supervisorctl('restart', '{}_postgresql'.format(purpose))
        wait_for_server_up(purpose)
    config = database_client_config(purpose)
    maintenance_config = postgresql_maintenance_config(purpose)
    env = os.environ.copy()
    env['PGPASSWORD'] = maintenance_config.owner_password
    if not database_existed(maintenance_config.version, config.host, config.port, maintenance_config.owner, config.database, env):
        return
    shell_execute('{pg_bin_dir}/dropdb -h {host} -p {port} -U {owner} {database}'.format(
        pg_bin_dir=get_pg_bin_dir(maintenance_config.version),
        host=config.host,
        port=config.port,
        owner=maintenance_config.owner,
        database=config.database), env=env, capture=True)


@script('migrate')
def migrate(purpose):
    wait_for_server_up(purpose)
    create_database_if_not_exists(purpose)
    enable_database_modules(purpose)
    enable_database_chinese_fts(purpose)
    versions = load_versions(purpose)
    db = lambda: require_database(purpose)

    @transactional(db)
    def execute_migration_scripts():
        create_database_migration_table_if_not_exists(purpose)
        current_version = db().get_scalar('''
            SELECT to_version
            FROM database_migration_event
            ORDER BY id DESC
            LIMIT 1
            ''') or 0
        from_version = current_version
        max_version = max(versions) if versions else None
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
            db().execute(versions[to_version].text('UTF-8'))
        db().insert('database_migration_event', from_version=from_version, to_version=to_version, migrated_at=get_current_time())
        LOGGER.info('[MIGRATE] migrated postgresql server: %(purpose)s from %(from_version)s to %(max_version)s', {
            'purpose': purpose,
            'from_version': from_version,
            'max_version': max_version
        })

    execute_migration_scripts()


def wait_for_server_up(purpose):
    version = postgresql_maintenance_config(purpose).version
    for i in range(20):
        try:
            psql(purpose, version, '-c "SELECT 1"', database='postgres', capture=True)
            break
        except Exception:
            import traceback
            traceback.print_exc()
            LOGGER.info('[MIGRATE] wait for postgresql...')
            time.sleep(3)


def database_existed(version, host, port, owner, database, env):
    output = shell_execute(
        '{}/psql -h {} -p {} -U {} -lqt | cut -d \| -f 1 | grep -w {} | wc -l'.format(get_pg_bin_dir(version), host, port, owner, database), env=env,
        capture=True, debug=True)
    return 1 == int(output)


@script('create-database')
def create_database_if_not_exists(purpose):
    config = database_client_config(purpose)
    maintenance_config = postgresql_maintenance_config(purpose)
    env = os.environ.copy()
    env['PGPASSWORD'] = maintenance_config.owner_password
    if database_existed(maintenance_config.version, config.host, config.port, maintenance_config.owner, config.database, env):
        return
    shell_execute('{pg_bin_dir}/createdb -h {host} -p {port} -U {owner} {database} -E UTF-8 --lc-collate=C --lc-ctype=C'.format(
        pg_bin_dir=get_pg_bin_dir(maintenance_config.version),
        host=config.host,
        port=config.port,
        owner=maintenance_config.owner,
        database=config.database), env=env, capture=True)
    # grant readonly privileges on the database to readonly user
    psql(purpose, maintenance_config.version, "-c '{}'".format('''
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO readonly;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly;
        '''), capture=True)


@script('enable-database-modules')
def enable_database_modules(purpose):
    config = database_client_config(purpose)
    if not config.enable_modules:
        return
    maintenance_config = postgresql_maintenance_config(purpose)
    env = os.environ.copy()
    env['PGPASSWORD'] = maintenance_config.owner_password
    commands = ''.join('CREATE EXTENSION IF NOT EXISTS {};'.format(module) for module in config.enable_modules)
    shell_execute(
        '{}/psql -h {} -p {} -U {} -d {} -c "{}"'.format(get_pg_bin_dir(maintenance_config.version), config.host, config.port, maintenance_config.owner,
                                                         config.database, commands), env=env, debug=True)


@script('enable-database-chinese-fts')
def enable_database_chinese_fts(purpose):
    config = database_client_config(purpose)
    if not config.enable_chinese_fts:
        return
    maintenance_config = postgresql_maintenance_config(purpose)
    env = os.environ.copy()
    env['PGPASSWORD'] = maintenance_config.owner_password
    if is_database_chinese_fts_enabled(maintenance_config.version, config.host, config.port, maintenance_config.owner, config.database, env):
        return
    commands = '''
        BEGIN;
        CREATE EXTENSION IF NOT EXISTS {ext_name};
        DROP TEXT SEARCH CONFIGURATION IF EXISTS {ext_config_name};
        CREATE TEXT SEARCH CONFIGURATION {ext_config_name} (PARSER={ext_name});
        ALTER TEXT SEARCH CONFIGURATION {ext_config_name} DROP MAPPING IF EXISTS FOR {token_types};
        ALTER TEXT SEARCH CONFIGURATION {ext_config_name} ADD MAPPING FOR {token_types} WITH {dictionary_name};
        COMMIT;
        '''.format(ext_name='zhparser', ext_config_name='zhparser_config', token_types='n,v,a,i,e,l', dictionary_name='simple')
    shell_execute('{}/psql -h {} -p {} -U {} -d {} -c "{}"'.format(get_pg_bin_dir(maintenance_config.version), config.host, config.port,
                                                                   maintenance_config.owner, config.database, commands), env=env, debug=True)


def is_database_chinese_fts_enabled(version, host, port, owner, database, env):
    output = shell_execute(
        '''{}/psql -h {} -p {} -U {} -d {} -Atc "SELECT 'ENABLED' FROM pg_extension WHERE extname='{}'"'''.format(
            get_pg_bin_dir(version), host, port, owner, database, 'zhparser'), env=env, capture=True, debug=True)
    return output and 'ENABLED' == output.splitlines()[-1]


def create_database_migration_table_if_not_exists(purpose):
    db = lambda: require_database(purpose)
    db().execute('''
        CREATE TABLE IF NOT EXISTS database_migration_event (
            id SERIAL PRIMARY KEY,
            from_version INT NOT NULL,
            to_version INT NOT NULL,
            migrated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            EXCLUDE USING GIST (NUMRANGE(from_version, to_version) WITH &&)
        )
        ''')


def psql(purpose, version, extra_arg, database=None, **kwargs):
    config = database_client_config(purpose)
    env = os.environ.copy()
    env['PGPASSWORD'] = config.password
    shell_execute('{pg_bin_dir}/psql -h {host} -p {port} -U {user} {extra_arg} --set ON_ERROR_STOP=1 -d {database}'.format(
        pg_bin_dir=get_pg_bin_dir(version),
        host=config.host,
        port=config.port,
        user=config.user,
        database=database or config.database,
        extra_arg=extra_arg), env=env, **kwargs)


@script('reset')
def reset(purpose):
    shell_execute('veil backend database postgresql drop-database {}'.format(purpose))
    shell_execute('veil backend database postgresql migrate {}'.format(purpose))
