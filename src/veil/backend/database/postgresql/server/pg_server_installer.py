from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

LOGGER = logging.getLogger(__name__)

@composite_installer
def postgresql_server_resource(purpose, config):
    pg_data_dir = get_data_dir(purpose)
    pg_config_dir = get_config_dir(purpose)
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        os_package_resource(name='postgresql-9.1'),
        os_service_resource(state='not_installed', name='postgresql', path='/etc/rc0.d/K21postgresql'),
        postgresql_global_bin_resource(),
        postgresql_cluster_resource(purpose=purpose, owner=config.owner, owner_password=config.owner_password),
        directory_resource(path=pg_config_dir),
        file_resource(
            path=pg_config_dir / 'postgresql.conf',
            content=render_config('postgresql.conf.j2', config={
                'data_directory': pg_data_dir,
                'host': config.host,
                'port': config.port,
                'log_destination': 'csvlog',
                'logging_collector': True,
                'log_directory': VEIL_LOG_DIR / '{}-postgresql'.format(purpose),
                'log_min_duration_statement': config.log_min_duration_statement
            })),
        file_resource(path=pg_config_dir / 'pg_hba.conf', content=render_config('pg_hba.conf.j2', host=config.host)),
        file_resource(path=pg_config_dir / 'pg_ident.conf', content=render_config('pg_ident.conf.j2')),
        file_resource(path=pg_config_dir / 'postgresql-maintenance.cfg', content=render_config(
            'postgresql-maintenance.cfg.j2', owner=config.owner, owner_password=config.owner_password)),
        symbolic_link_resource(path=pg_data_dir / 'postgresql.conf', to=pg_config_dir / 'postgresql.conf'),
        symbolic_link_resource(path=pg_data_dir / 'pg_hba.conf', to=pg_config_dir / 'pg_hba.conf'),
        symbolic_link_resource(path=pg_data_dir / 'pg_ident.conf', to=pg_config_dir / 'pg_ident.conf'),
        postgresql_user_resource(purpose=purpose, user=config.user, password=config.password,
            owner=config.owner, owner_password=config.owner_password,
            host=config.host, port=config.port)
    ])
    return resources


@composite_installer
def postgresql_global_bin_resource():
    pg_bin_dir = as_path('/usr/lib/postgresql/9.1/bin')
    global_bin_dir = as_path('/usr/bin')
    resources = [
        symbolic_link_resource(path=global_bin_dir / 'psql', to='{}/psql'.format(pg_bin_dir)),
        symbolic_link_resource(path=global_bin_dir / 'pg_dump', to='{}/pg_dump'.format(pg_bin_dir)),
        symbolic_link_resource(path=global_bin_dir / 'initdb', to='{}/initdb'.format(pg_bin_dir)),
        symbolic_link_resource(path=global_bin_dir / 'pg_ctl', to='{}/pg_ctl'.format(pg_bin_dir)),
        symbolic_link_resource(path=global_bin_dir / 'postgres', to='{}/postgres'.format(pg_bin_dir))
    ]
    return resources


@atomic_installer
def postgresql_cluster_resource(purpose, owner, owner_password):
    pg_data_dir = get_data_dir(purpose)
    is_installed = pg_data_dir.exists()
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['postgresql_initdb?{}'.format(purpose)] = '-' if is_installed else 'INSTALL'
        return
    if is_installed:
        return
    old_permission = shell_execute("stat -c '%a' {}".format(pg_data_dir.dirname()), capture=True).strip()
    shell_execute('chmod 777 {}'.format(pg_data_dir.dirname()))
    do_install(file_resource(path='/tmp/pg-owner-password', content=owner_password))
    try:
        shell_execute(
            'su {pg_data_owner} -c "initdb  -E {encoding} --locale=en_US.UTF-8 -A md5 -U {pg_data_owner} --pwfile=/tmp/pg-owner-password {pg_data_dir}"'.format(
                encoding='UTF8', pg_data_owner=owner, pg_data_dir=pg_data_dir
            ))
    finally:
        delete_file('/tmp/pg-owner-password')
    shell_execute('chmod {} {}'.format(old_permission, pg_data_dir.dirname()))
    delete_file(pg_data_dir / 'postgresql.conf')
    delete_file(pg_data_dir / 'pg_hba.conf')
    delete_file(pg_data_dir / 'pg_ident.conf')


@atomic_installer
def postgresql_user_resource(purpose, user, password, owner, owner_password, host, port):
    pg_user = user
    assert pg_user, 'must specify postgresql user'
    pg_password = password
    assert pg_password, 'must specify postgresql user password'
    pg_data_dir = get_data_dir(purpose)
    user_installed_tag_file = pg_data_dir / 'user-installed'
    is_installed = user_installed_tag_file.exists()
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['postgresql_user?{}'.format(purpose)] = '-' if is_installed else 'INSTALL'
        return
    if is_installed:
        return
    with postgresql_server_running(pg_data_dir, owner):
        env = os.environ.copy()
        env['PGPASSWORD'] = owner_password
        try:
            shell_execute('psql -h {} -p {} -U {} -d postgres -c "{}"'.format(
                host, port, owner,
                "CREATE USER {} WITH PASSWORD '{}'".format(pg_user, pg_password)
            ), env=env, capture=True)
            user_installed_tag_file.touch()
        except ShellExecutionError, e:
            if 'already exists' in e.output:
                user_installed_tag_file.touch()
            else:
                raise


def delete_file(path):
    if os.path.exists(path):
        LOGGER.info('delete file: %(path)s', {'path': path})
        os.remove(path)


@contextlib.contextmanager
def postgresql_server_running(data_directory, owner):
    shell_execute('su {} -c "pg_ctl -D {} start"'.format(
        owner, data_directory))
    time.sleep(5)
    try:
        yield
    finally:
        shell_execute('su {} -c "pg_ctl -D {} stop"'.format(
            owner, data_directory))


def load_postgresql_maintenance_config(purpose):
    config_dir = get_config_dir(purpose)
    return load_config_from(config_dir / 'postgresql-maintenance.cfg',
        'owner', 'owner_password')


def get_config_dir(purpose):
    return VEIL_ETC_DIR / '{}-postgresql'.format(purpose.replace('_', '-'))


def get_data_dir(purpose):
    return VEIL_VAR_DIR / '{}-postgresql'.format(purpose.replace('_', '-'))