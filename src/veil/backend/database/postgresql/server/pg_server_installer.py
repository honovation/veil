from __future__ import unicode_literals, print_function, division
import sys
from veil.profile.installer import *
from ...postgresql_setting import get_pg_config_dir, get_pg_data_dir, get_pg_bin_dir
from .pg_fts_chinese import scws_resource, zhparser_resource

LOGGER = logging.getLogger(__name__)


@composite_installer
def postgresql_server_resource(purpose, config):
    upgrading = False
    maintenance_config = postgresql_maintenance_config(purpose, must_exist=False)
    if maintenance_config and maintenance_config.version != config.version:
        assert maintenance_config.version < config.version, 'cannot downgrade postgresql server from {} to {}'.format(maintenance_config.version,
            config.version)
        upgrading = True
        LOGGER.warn('Start to install new-version postgresql server: %(old_version)s => %(new_version)s', {
            'old_version': maintenance_config.version,
            'new_version': config.version
        })

    pg_data_dir = get_pg_data_dir(purpose, config.version)
    pg_config_dir = get_pg_config_dir(purpose, config.version)
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        postgresql_apt_repository_resource(),
        # remove cmd_run_before_install at below at next PostgreSQL server upgrade
        os_package_resource(name='postgresql-{}'.format(config.version), cmd_run_before_install='rm -f /etc/sysctl.d/30-postgresql-shm.conf')])
    resources.extend([
        os_service_resource(state='not_installed', name='postgresql'),
        postgresql_cluster_resource(purpose=purpose, version=config.version, owner=config.owner, owner_password=config.owner_password),
        directory_resource(path=pg_config_dir),
        file_resource(
            path=pg_config_dir / 'postgresql.conf',
            content=render_config('postgresql.conf.j2', config={
                'purpose': purpose,
                'version': config.version,
                'data_directory': pg_data_dir,
                'host': config.host,
                'port': config.port,
                'log_destination': 'csvlog',
                'logging_collector': True,
                'log_directory': VEIL_LOG_DIR / '{}-postgresql'.format(purpose.replace('_', '-')),
                'shared_buffers': config.shared_buffers,
                'work_mem': config.work_mem,
                'maintenance_work_mem': config.maintenance_work_mem,
                'effective_io_concurrency': config.effective_io_concurrency,
                'checkpoint_segments': config.checkpoint_segments,
                'checkpoint_completion_target': config.checkpoint_completion_target,
                'effective_cache_size': config.effective_cache_size,
                'log_min_duration_statement': config.log_min_duration_statement,
                'log_filename': config.get('log_filename')
            })),
        file_resource(path=pg_config_dir / 'pg_hba.conf', content=render_config('pg_hba.conf.j2', host=config.host)),
        file_resource(path=pg_config_dir / 'pg_ident.conf', content=render_config('pg_ident.conf.j2')),
        file_resource(path=pg_config_dir / 'postgresql-maintenance.cfg', content=render_config(
            'postgresql-maintenance.cfg.j2', version=config.version, owner=config.owner, owner_password=config.owner_password)),
        symbolic_link_resource(path=get_pg_config_dir(purpose), to=pg_config_dir),
        symbolic_link_resource(path=pg_data_dir / 'postgresql.conf', to=pg_config_dir / 'postgresql.conf'),
        symbolic_link_resource(path=pg_data_dir / 'pg_hba.conf', to=pg_config_dir / 'pg_hba.conf'),
        symbolic_link_resource(path=pg_data_dir / 'pg_ident.conf', to=pg_config_dir / 'pg_ident.conf'),
    ])
    if upgrading:
        resources.extend([
            os_package_resource(name='postgresql-server-dev-{}'.format(config.version)),
            postgresql_cluster_upgrading_resource(purpose=purpose, old_version=maintenance_config.version, new_version=config.version,
                host=config.host, port=config.port, owner=config.owner, owner_password=config.owner_password)
        ])
    resources.extend([
        postgresql_user_resource(purpose=purpose, version=config.version, host=config.host, port=config.port, owner=config.owner,
            owner_password=config.owner_password, user=config.user, password=config.password),
        postgresql_user_resource(purpose=purpose, version=config.version, host=config.host, port=config.port, owner=config.owner,
            owner_password=config.owner_password, user='readonly', password='r1adonly', readonly=True)
    ])
    if config.enable_chinese_fts:
        resources.extend([
            os_package_resource(name='postgresql-server-dev-{}'.format(config.version)),
            scws_resource(),
            zhparser_resource()
        ])

    return resources


@atomic_installer
def postgresql_cluster_upgrading_resource(purpose, old_version, new_version, host, port, owner, owner_password):
    pg_data_dir = get_pg_data_dir(purpose, new_version)
    installed = pg_data_dir.exists()
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['postgresql_cluster_upgrading?{}'.format(purpose)] = '-' if installed else 'INSTALL'
        return
    if installed:
        return
    upgrade_postgresql_cluster(purpose, old_version, new_version, owner, check_only=True)
    if not confirm_postgresql_cluster_upgrading(old_version, new_version):
        return
    upgrade_postgresql_cluster(purpose, old_version, new_version, owner, check_only=False)
    vacuum_upgraded_postgresql_cluster(purpose, new_version, host, port, owner, owner_password)
    display_postgresql_cluster_post_upgrade_instructions()


def upgrade_postgresql_cluster(purpose, old_version, new_version, owner, check_only=True):
    if check_only:
        LOGGER.warn('Checking postgresql server upgrading: %(old_version)s => %(new_version)s', {
            'old_version': old_version, 'new_version': new_version
        })
    else:
        LOGGER.warn('Upgrading postgresql server: %(old_version)s => %(new_version)s', {'old_version': old_version, 'new_version': new_version})
    shell_execute('''
        su - {pg_data_owner} -c '{new_bin_dir}/pg_upgrade {check_only} -v -j {cpu_cores} -u {pg_data_owner} -b {old_bin_dir} -B {new_bin_dir} -d {old_data_dir} -D {new_data_dir} -o "-c config_file={old_data_dir}/postgresql.conf" -O "-c config_file={new_data_dir}/postgresql.conf"'
        '''.format(
        pg_data_owner=owner, check_only='-c' if check_only else '', cpu_cores=shell_execute('nproc', capture=True),
        old_bin_dir=get_pg_bin_dir(old_version), old_data_dir=get_pg_data_dir(purpose, old_version),
        new_bin_dir=get_pg_bin_dir(new_version), new_data_dir=get_pg_data_dir(purpose, new_version)
    ), capture=True)


def vacuum_upgraded_postgresql_cluster(purpose, version, host, port, owner, owner_password):
    LOGGER.warn('Vacuum postgresql server after upgrading')
    pg_data_dir = get_pg_data_dir(purpose, version)
    with postgresql_server_running(version, pg_data_dir, owner):
        env = os.environ.copy()
        env['PGPASSWORD'] = owner_password
        shell_execute("su {pg_data_owner} -c '{pg_bin_dir}/vacuumdb -h {host} -p {port} -U {pg_data_owner} -a -f -F -z'".format(
            pg_data_owner=owner, pg_bin_dir=get_pg_bin_dir(version), host=host, port=port), capture=True, env=env)


def confirm_postgresql_cluster_upgrading(old_version, new_version):
    msg_to_upgrade = 'upgrade postgresql server from {} to {}'.format(old_version, new_version)
    msg_to_not_upgrade = 'cancel upgrading'
    print('type "{}" to continue or "{}" to not upgrade:'.format(msg_to_upgrade, msg_to_not_upgrade))
    while True:
        instruction = sys.stdin.readline().strip()
        if msg_to_upgrade == instruction:
            return True
        elif msg_to_not_upgrade == instruction:
            return False


def display_postgresql_cluster_post_upgrade_instructions():
    print('!!! IMPORTANT !!!')
    print('''Please do the following post-Upgrade processing:
        1.Verify the application
        2.Delete old cluster: config and data directories
        3.Remove the installation of the old-version postgresql server
        ''')
    print('type "i will do it" without space to continue:')
    while True:
        if 'iwilldoit' == sys.stdin.readline().strip():
            break


@atomic_installer
def postgresql_cluster_resource(purpose, version, owner, owner_password):
    pg_data_dir = get_pg_data_dir(purpose, version)
    installed = pg_data_dir.exists()
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['postgresql_initdb?{}'.format(purpose)] = '-' if installed else 'INSTALL'
        return
    if installed:
        return
    LOGGER.info('install postgresql cluster: for %(purpose)s, %(version)s', {'purpose': purpose, 'version': version})
    old_permission = shell_execute("stat -c '%a' {}".format(pg_data_dir.parent), capture=True)
    shell_execute('chmod 777 {}'.format(pg_data_dir.parent), capture=True)
    install_resource(file_resource(path='/tmp/pg-{}-owner-password'.format(purpose), content=owner_password))
    try:
        shell_execute('usermod -a -G postgres {}'.format(owner))
        shell_execute(
            'su {pg_data_owner} -c "{pg_bin_dir}/initdb -E UTF-8 --locale=zh_CN.UTF-8 --lc-collate=C --lc-ctype=C -A md5 -U {pg_data_owner} --pwfile=/tmp/pg-{purpose}-owner-password {pg_data_dir}"'.format(
                pg_data_owner=owner, pg_bin_dir=get_pg_bin_dir(version), pg_data_dir=pg_data_dir, purpose=purpose
            ), capture=True)
        shell_execute('mv postgresql.conf postgresql.conf.origin', cwd=pg_data_dir)
        shell_execute('mv pg_hba.conf pg_hba.conf.origin', cwd=pg_data_dir)
        shell_execute('mv pg_ident.conf pg_ident.conf.origin', cwd=pg_data_dir)
    finally:
        delete_file('/tmp/pg-{}-owner-password'.format(purpose))
        shell_execute('chmod {} {}'.format(old_permission, pg_data_dir.parent), capture=True)


@atomic_installer
def postgresql_user_resource(purpose, version, host, port, owner, owner_password, user, password, readonly=False):
    assert user, 'must specify postgresql user'
    assert password, 'must specify postgresql user password'
    pg_data_dir = get_pg_data_dir(purpose, version)
    user_installed_tag_file = pg_data_dir / 'user-{}-installed'.format(user)
    installed = user_installed_tag_file.exists()
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['postgresql_user?{}'.format(purpose)] = '-' if installed else 'INSTALL'
        return
    if installed:
        return
    LOGGER.info('install postgresql user: %(user)s in %(purpose)s', {'user': user, 'purpose': purpose})
    pg_bin_dir = get_pg_bin_dir(version)
    with postgresql_server_running(version, pg_data_dir, owner):
        env = os.environ.copy()
        env['PGPASSWORD'] = owner_password
        if not postgresql_user_existed(version, host, port, owner, user, env):
            if readonly:
                shell_execute('''
                    {}/psql -h {} -p {} -U {} -d postgres -c "CREATE USER {} WITH PASSWORD '{}'; ALTER USER {} SET default_transaction_read_only=on;"
                    '''.format(pg_bin_dir, host, port, owner, user, password, user), env=env, capture=True)
            else:
                shell_execute('''
                    {}/psql -h {} -p {} -U {} -d postgres -c "CREATE USER {} WITH PASSWORD '{}'"
                    '''.format(pg_bin_dir, host, port, owner, user, password), env=env, capture=True)
        user_installed_tag_file.touch()


def postgresql_user_existed(version, host, port, owner, user, env):
    return '1' == shell_execute('''
        {}/psql -h {} -p {} -U {} -d postgres -tAc "SELECT 1 FROM pg_user WHERE usename='{}'"
        '''.format(get_pg_bin_dir(version), host, port, owner, user), env=env, capture=True)


def delete_file(path):
    if os.path.exists(path):
        LOGGER.info('delete file: %(path)s', {'path': path})
        os.remove(path)


@contextlib.contextmanager
def postgresql_server_running(version, data_directory, owner):
    # create socket directory for postgresql if not exists
    try:
        shell_execute('getent passwd postgres')
    except ShellExecutionError:
        pass
    else:
        shell_execute('install -d -m 2775 -o postgres -g postgres /var/run/postgresql')
    pg_bin_dir = get_pg_bin_dir(version)
    shell_execute('su {} -c "{}/pg_ctl -D {} start"'.format(owner, pg_bin_dir, data_directory))
    time.sleep(5)
    try:
        yield
    finally:
        shell_execute('su {} -c "{}/pg_ctl -D {} stop"'.format(owner, pg_bin_dir, data_directory))


_maintenance_config = {}
def postgresql_maintenance_config(purpose, must_exist=True):
    if purpose not in _maintenance_config:
        _maintenance_config[purpose] = load_postgresql_maintenance_config(purpose, must_exist)
    return _maintenance_config[purpose]


def load_postgresql_maintenance_config(purpose, must_exist):
    maintenance_config_path = get_pg_config_dir(purpose) / 'postgresql-maintenance.cfg'
    if not must_exist and not maintenance_config_path.exists():
        return DictObject()
    return load_config_from(maintenance_config_path, 'version', 'owner', 'owner_password')
