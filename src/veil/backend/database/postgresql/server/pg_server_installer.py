from __future__ import unicode_literals, print_function, division
import sys
from decimal import Decimal
from veil.profile.installer import *
from ...postgresql_setting import get_pg_config_dir, get_pg_data_dir, get_pg_bin_dir
from .pg_fts_chinese import scws_resource, zhparser_resource

LOGGER = logging.getLogger(__name__)


@composite_installer
def postgresql_server_resource(config):
    upgrading = False
    maintenance_config = postgresql_maintenance_config(config.purpose, must_exist=False)
    if maintenance_config and maintenance_config.version != config.version:
        assert Decimal(maintenance_config.version) < Decimal(config.version), 'cannot downgrade postgresql server from {} to {}'.format(
            maintenance_config.version, config.version)
        upgrading = True
        LOGGER.warn('Start to install new-version postgresql server: %(old_version)s => %(new_version)s', {
            'old_version': maintenance_config.version,
            'new_version': config.version
        })

    pg_data_dir = get_pg_data_dir(config.purpose, config.version)
    pg_config_dir = get_pg_config_dir(config.purpose, config.version)
    pg_config = dict(config, data_directory=pg_data_dir, log_directory=VEIL_LOG_DIR / '{}-postgresql'.format(config.purpose.replace('_', '-')))
    resources = [
        postgresql_apt_repository_resource(),
        os_package_resource(name='postgresql-{}'.format(config.version)),
        os_service_auto_starting_resource(name='postgresql', state='not_installed'),
        postgresql_cluster_resource(purpose=config.purpose, version=config.version, owner=config.owner, owner_password=config.owner_password),
        directory_resource(path=pg_config_dir, owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        file_resource(
            path=pg_config_dir / 'postgresql.conf',
            content=render_config('postgresql.conf.j2', config=pg_config), owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        file_resource(path=pg_config_dir / 'pg_hba.conf', content=render_config('pg_hba.conf.j2', host=config.host, replication_user=config.replication_user,
                                                                                replication_host=config.replication_host),
                      owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        file_resource(path=pg_config_dir / 'pg_ident.conf', content=render_config('pg_ident.conf.j2'), owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        file_resource(path=pg_config_dir / 'postgresql-maintenance.cfg',
                      content=render_config('postgresql-maintenance.cfg.j2', version=config.version, owner=config.owner, owner_password=config.owner_password),
                      owner=CURRENT_USER, group=CURRENT_USER_GROUP),
        symbolic_link_resource(path=pg_data_dir / 'postgresql.conf', to=pg_config_dir / 'postgresql.conf'),
        symbolic_link_resource(path=pg_data_dir / 'pg_hba.conf', to=pg_config_dir / 'pg_hba.conf'),
        symbolic_link_resource(path=pg_data_dir / 'pg_ident.conf', to=pg_config_dir / 'pg_ident.conf'),
    ]
    if upgrading or config.enable_chinese_fts:
        resources.append(os_package_resource(name='postgresql-server-dev-{}'.format(config.version)))
    if config.enable_chinese_fts:
        resources.extend([
            scws_resource(),
            zhparser_resource(reinstall=upgrading)
        ])
    if upgrading:
        resources.append(postgresql_cluster_upgrading_resource(purpose=config.purpose, old_version=maintenance_config.version, new_version=config.version,
                                                               host=config.host, port=config.port, owner=config.owner, owner_password=config.owner_password))
    resources.extend([
        symbolic_link_resource(path=get_pg_config_dir(config.purpose), to=pg_config_dir),
        postgresql_user_resource(purpose=config.purpose, version=config.version, host=config.host, port=config.port, owner=config.owner,
                                 owner_password=config.owner_password, user=config.user, password=config.password),
        postgresql_user_resource(purpose=config.purpose, version=config.version, host=config.host, port=config.port, owner=config.owner,
                                 owner_password=config.owner_password, user='readonly', password='r1adonly', readonly=True)
    ])
    if config.replication_user:
        resources.extend([
            postgresql_user_resource(purpose=config.purpose, version=config.version, host=config.host, port=config.port, owner=config.owner,
                                     owner_password=config.owner_password, user=config.replication_user, replication=True),
            postgresql_user_resource(purpose=config.purpose, version=config.version, host=config.host, port=config.port, owner=config.owner,
                                     owner_password=config.owner_password, user='barman', superuser=True),
            postgresql_physical_replication_slot_resource(purpose=config.purpose, version=config.version, host=config.host, port=config.port,
                                                          owner=config.owner, owner_password=config.owner_password, slot_name='barman')
        ])

    return resources


@atomic_installer
def postgresql_cluster_upgrading_resource(purpose, old_version, new_version, host, port, owner, owner_password):
    installed = is_postgresql_cluster_upgraded(purpose, new_version, host, port, owner, owner_password)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['postgresql_cluster_upgrading?{}'.format(purpose)] = '-' if installed else 'INSTALL'
        return
    if installed:
        return
    upgrade_postgresql_cluster(purpose, old_version, new_version, owner, owner_password, check_only=True)
    if not confirm_postgresql_cluster_upgrading(old_version, new_version):
        raise Exception('user canceled upgrading postgresql')
    upgrade_postgresql_cluster(purpose, old_version, new_version, owner, owner_password, check_only=False)
    vacuum_upgraded_postgresql_cluster(purpose, new_version, host, port, owner, owner_password)
    display_postgresql_cluster_post_upgrade_instructions()


def is_postgresql_cluster_upgraded(purpose, version, host, port, owner, owner_password):
    LOGGER.warn('Checking if postgresql cluster upgraded')
    pg_data_dir = get_pg_data_dir(purpose, version)
    with postgresql_server_running(version, pg_data_dir, owner):
        env = os.environ.copy()
        env['PGPASSWORD'] = owner_password
        output = shell_execute(
            "{}/psql -h {} -p {} -U {} -d postgres -Atc 'SELECT COUNT(*) FROM pg_database'".format(get_pg_bin_dir(version), host, port, owner), env=env,
            capture=True, debug=True)
        return int(output) > 3


def upgrade_postgresql_cluster(purpose, old_version, new_version, owner, owner_password, check_only=True):
    if check_only:
        LOGGER.warn('Checking postgresql server upgrading: %(old_version)s => %(new_version)s', {
            'old_version': old_version, 'new_version': new_version
        })
    else:
        LOGGER.warn('Upgrading postgresql server: %(old_version)s => %(new_version)s', {'old_version': old_version, 'new_version': new_version})
    pg_upgrade_env = {'PGPASSWORD': owner_password}
    pg_upgrade_command = (
        '{new_bin_dir}/pg_upgrade '
        '{check_only} '
        '-v '
        '-j `nproc` '
        '-U {pg_data_owner} '
        '-b {old_bin_dir} '
        '-B {new_bin_dir} '
        '-d {old_data_dir} '
        '-D {new_data_dir} '
        "-o '-c config_file={old_data_dir}/postgresql.conf' "
        "-O '-c config_file={new_data_dir}/postgresql.conf'".format(pg_data_owner=owner, check_only='-c' if check_only else '',
                                                                    old_bin_dir=get_pg_bin_dir(old_version), old_data_dir=get_pg_data_dir(purpose, old_version),
                                                                    new_bin_dir=get_pg_bin_dir(new_version), new_data_dir=get_pg_data_dir(purpose, new_version))
    )
    shell_execute('sudo su {pg_data_owner_os} -c "{pg_upgrade_command}"'.format(pg_data_owner_os=CURRENT_USER, pg_upgrade_command=pg_upgrade_command),
                  env=pg_upgrade_env, capture=True)


def vacuum_upgraded_postgresql_cluster(purpose, version, host, port, owner, owner_password):
    LOGGER.warn('Vacuum postgresql server after upgrading')
    pg_data_dir = get_pg_data_dir(purpose, version)
    with postgresql_server_running(version, pg_data_dir, owner):
        env = os.environ.copy()
        env['PGPASSWORD'] = owner_password
        shell_execute('{pg_bin_dir}/vacuumdb -h {host} -p {port} -U {pg_data_owner} -j `nproc` -a -F -z'.format(
            pg_bin_dir=get_pg_bin_dir(version), pg_data_owner=owner, host=host, port=port), env=env, capture=True)


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
    print('''Please do the following post-Upgrade processing (check https://github.com/honovation/ljmall/issues/1173 for detail):
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
    # run the below idempotent command even the resource has been installed, and it is necessary for the case that lxc container is recreated.
    shell_execute('sudo usermod -a -G postgres {}'.format(CURRENT_USER))
    if installed:
        return
    LOGGER.info('install postgresql cluster: for %(purpose)s, %(version)s', {'purpose': purpose, 'version': version})
    old_permission = shell_execute("stat -c '%a' {}".format(pg_data_dir.parent), capture=True)
    shell_execute('chmod 0777 {}'.format(pg_data_dir.parent), capture=True)
    install_resource(file_resource(path='/tmp/pg-{}-owner-password'.format(purpose), content=owner_password, owner=CURRENT_USER, group=CURRENT_USER_GROUP))
    initdb_command = (
        '{pg_bin_dir}/initdb '
        '--data-checksums '
        '-E UTF-8 '
        '--locale=C.UTF-8 '
        '-A md5 '
        '-U {pg_data_owner} '
        '--pwfile=/tmp/pg-{purpose}-owner-password '
        '{pg_data_dir}'.format(pg_data_owner=owner, pg_bin_dir=get_pg_bin_dir(version), pg_data_dir=pg_data_dir, purpose=purpose)
    )
    try:
        shell_execute('sudo su {pg_data_owner_os} -c "{initdb_command}"'.format(pg_data_owner_os=CURRENT_USER, initdb_command=initdb_command), capture=True)
        shell_execute('mv -n postgresql.conf postgresql.conf.origin', cwd=pg_data_dir)
        shell_execute('mv -n pg_hba.conf pg_hba.conf.origin', cwd=pg_data_dir)
        shell_execute('mv -n pg_ident.conf pg_ident.conf.origin', cwd=pg_data_dir)
    finally:
        delete_file('/tmp/pg-{}-owner-password'.format(purpose))
        shell_execute('chmod {} {}'.format(old_permission, pg_data_dir.parent), capture=True)


@atomic_installer
def postgresql_user_resource(purpose, version, host, port, owner, owner_password, user, password=None, readonly=False, replication=False, superuser=False):
    assert user, 'must specify postgresql user'
    assert replication or superuser or password is not None, 'must specify postgresql user password for non replication or non superuser mode'
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
            elif replication:
                shell_execute('''
                    {}/psql -h {} -p {} -U {} -d postgres -c "CREATE USER {} WITH REPLICATION;"
                    '''.format(pg_bin_dir, host, port, owner, user), env=env, capture=True)
            elif superuser:
                shell_execute('''
                    {}/psql -h {} -p {} -U {} -d postgres -c "CREATE USER {} WITH SUPERUSER;"
                    '''.format(pg_bin_dir, host, port, owner, user), env=env, capture=True)
            else:
                shell_execute('''
                    {}/psql -h {} -p {} -U {} -d postgres -c "CREATE USER {} WITH PASSWORD '{}'"
                    '''.format(pg_bin_dir, host, port, owner, user, password), env=env, capture=True)
        user_installed_tag_file.touch()


def postgresql_user_existed(version, host, port, owner, user, env):
    return '1' == shell_execute('''
        {}/psql -h {} -p {} -U {} -d postgres -tAc "SELECT 1 FROM pg_user WHERE usename='{}'"
        '''.format(get_pg_bin_dir(version), host, port, owner, user), env=env, capture=True)


@atomic_installer
def postgresql_physical_replication_slot_resource(purpose, version, host, port, owner, owner_password, slot_name):
    pg_data_dir = get_pg_data_dir(purpose, version)
    slot_installed_tag_file = pg_data_dir / 'physical-replication-slot-{}-installed'.format(slot_name)
    installed = slot_installed_tag_file.exists()
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['postgresql_physical_replication_slot?{}'.format(purpose)] = '-' if installed else 'INSTALL'
        return
    if installed:
        return
    LOGGER.info('install postgresql physical replication slot: %(slot_name)s in %(purpose)s', {'slot_name': slot_name, 'purpose': purpose})
    pg_bin_dir = get_pg_bin_dir(version)
    with postgresql_server_running(version, pg_data_dir, owner):
        env = os.environ.copy()
        env['PGPASSWORD'] = owner_password
        if not postgresql_physical_replication_slot_existed(version, host, port, owner, slot_name, env):
            shell_execute('''
                {}/psql -h {} -p {} -U {} -d postgres -c "SELECT * FROM PG_CREATE_PHYSICAL_REPLICATION_SLOT('{}')"
                '''.format(pg_bin_dir, host, port, owner, slot_name), env=env, capture=True)
        slot_installed_tag_file.touch()


def postgresql_physical_replication_slot_existed(version, host, port, owner, slot_name, env):
    return '1' == shell_execute('''
        {}/psql -h {} -p {} -U {} -d postgres -tAc "SELECT 1 FROM pg_replication_slots WHERE slot_name='{}' AND slot_type='physical'"
        '''.format(get_pg_bin_dir(version), host, port, owner, slot_name), env=env, capture=True)


def delete_file(path):
    if os.path.exists(path):
        LOGGER.info('delete file: %(path)s', {'path': path})
        os.remove(path)


@contextlib.contextmanager
def postgresql_server_running(version, data_directory, owner):
    pg_bin_dir = get_pg_bin_dir(version)
    shell_execute('sudo su {} -c "{}/pg_ctl -D {} start"'.format(CURRENT_USER, pg_bin_dir, data_directory))
    time.sleep(5)
    try:
        yield
    finally:
        shell_execute('sudo su {} -c "{}/pg_ctl -D {} stop"'.format(CURRENT_USER, pg_bin_dir, data_directory))


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
