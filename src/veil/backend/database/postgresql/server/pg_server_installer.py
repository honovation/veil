from __future__ import unicode_literals, print_function, division
import os
import contextlib
import time
import logging
from veil.backend.shell import *
from veil.environment import *
from veil.environment.setting import *
from veil.utility.path import *
from veil.frontend.template import *
from veil_installer import *

LOGGER = logging.getLogger(__name__)

@installer('postgresql')
@using_template
def install_postgresql_server(dry_run_result, name):
    settings = get_settings()
    config = getattr(settings, '{}_postgresql'.format(name))
    pg_data_dir = as_path(config.data_directory)
    pg_config_dir = as_path(config.config_directory)
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        os_package_resource('postgresql-9.1'),
        os_service_resource(state='not_installed', name='postgresql', path='/etc/rc0.d/K21postgresql'),
        ('postgresql_global_bin', dict()),
        ('postgresql_initdb', dict(name=name)),
        directory_resource(pg_config_dir),
        file_resource(
            pg_config_dir / 'postgresql.conf',
            content=get_template('postgresql.conf.j2').render(config=config)),
        file_resource(pg_config_dir / 'pg_hba.conf', content=get_template('pg_hba.conf.j2').render(config=config)),
        file_resource(pg_config_dir / 'pg_ident.conf', content=get_template('pg_ident.conf.j2').render()),
        symbolic_link_resource(pg_data_dir / 'postgresql.conf', to=pg_config_dir / 'postgresql.conf'),
        symbolic_link_resource(pg_data_dir / 'pg_hba.conf', to=pg_config_dir / 'pg_hba.conf'),
        symbolic_link_resource(pg_data_dir / 'pg_ident.conf', to=pg_config_dir / 'pg_ident.conf'),
        ('postgresql_user', dict(name=name))
    ])
    return [], resources


@installer('postgresql_global_bin')
def install_postgresql_global_bin(dry_run_result):
    pg_bin_dir = as_path('/usr/lib/postgresql/9.1/bin')
    global_bin_dir = as_path('/usr/bin')
    resources = [
        symbolic_link_resource(global_bin_dir / 'psql', to='{}/psql'.format(pg_bin_dir)),
        symbolic_link_resource(global_bin_dir / 'pg_dump', to='{}/pg_dump'.format(pg_bin_dir)),
        symbolic_link_resource(global_bin_dir / 'initdb', to='{}/initdb'.format(pg_bin_dir)),
        symbolic_link_resource(global_bin_dir / 'pg_ctl', to='{}/pg_ctl'.format(pg_bin_dir)),
        symbolic_link_resource(global_bin_dir / 'postgres', to='{}/postgres'.format(pg_bin_dir))
    ]
    return [], resources


@installer('postgresql_initdb')
def install_postgresql_initdb(dry_run_result, name):
    settings = get_settings()
    config = getattr(settings, '{}_postgresql'.format(name))
    pg_data_dir = as_path(config.data_directory)
    is_installed = pg_data_dir.exists()
    if dry_run_result is not None:
        dry_run_result['postgresql_initdb?{}'.format(name)] = '-' if is_installed else 'INSTALL'
        return
    if is_installed:
        return
    old_permission = shell_execute("stat -c '%a' {}".format(pg_data_dir.dirname()), capture=True).strip()
    shell_execute('chmod 777 {}'.format(pg_data_dir.dirname()))
    install_file(None, path='/tmp/pg-owner-password', content=config.owner_password)
    try:
        shell_execute(
            'su {pg_data_owner} -c "initdb  -E {encoding} --locale=en_US.UTF-8 -A md5 -U {pg_data_owner} --pwfile=/tmp/pg-owner-password {pg_data_dir}"'.format(
                encoding='UTF8', pg_data_owner=config.owner, pg_data_dir=pg_data_dir
            ))
    finally:
        delete_file('/tmp/pg-owner-password')
    shell_execute('chmod {} {}'.format(old_permission, pg_data_dir.dirname()))
    delete_file(pg_data_dir / 'postgresql.conf')
    delete_file(pg_data_dir / 'pg_hba.conf')
    delete_file(pg_data_dir / 'pg_ident.conf')


@installer('postgresql_user')
def install_postgresql_user(dry_run_result, name):
    settings = get_settings()
    config = getattr(settings, '{}_postgresql'.format(name))
    pg_user = config.user
    assert pg_user, 'must specify postgresql user'
    pg_password = config.password
    assert pg_password, 'must specify postgresql user password'
    pg_data_dir = as_path(config.data_directory)
    user_installed_tag_file = pg_data_dir / 'user-installed'
    is_installed = user_installed_tag_file.exists()
    if dry_run_result is not None:
        dry_run_result['postgresql_user?{}'.format(name)] = '-' if is_installed else 'INSTALL'
        return
    if is_installed:
        return
    with postgresql_server_running(config):
        env = os.environ.copy()
        env['PGPASSWORD'] = config.owner_password
        shell_execute('psql -h {} -p {} -U {} -d postgres -c "{}"'.format(
            config.host, config.port, config.owner,
            "CREATE USER {} WITH PASSWORD '{}'".format(pg_user, pg_password)
        ), env=env)
        user_installed_tag_file.touch()


def delete_file(path):
    if os.path.exists(path):
        LOGGER.info('delete {}'.format(path))
        os.remove(path)


@contextlib.contextmanager
def postgresql_server_running(config):
    shell_execute('su {} -c "pg_ctl -D {} start"'.format(
        config.owner, config.data_directory))
    time.sleep(5)
    try:
        yield
    finally:
        shell_execute('su {} -c "pg_ctl -D {} stop"'.format(
            config.owner, config.data_directory))