# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

env = os.environ.copy()

ORACLE_HOME = '/opt/instantclient_11_2'
LD_LIBRARY_PATH = '{}:{}'.format(env.get('LD_LIBRARY_PATH', ''), ORACLE_HOME)
CX_ORACLE_HOME = '/opt/cx_Oracle-5.1.2'


@atomic_installer
def oracle_driver_resource():
    installed_version = get_python_package_installed_version('cx-Oracle')
    action = None if installed_version else 'INSTALL'
    if UPGRADE_MODE_LATEST == get_upgrade_mode():
        action = action or 'UPGRADE'
    elif UPGRADE_MODE_FAST == get_upgrade_mode():
        latest_version = get_resource_latest_version('veil.backend.database.oracle_driver.oracle_driver_resource')
        action = action or (None if latest_version == installed_version else 'UPGRADE')
    elif UPGRADE_MODE_NO == get_upgrade_mode():
        pass
    else:
        raise NotImplementedError()

    env['ORACLE_HOME'] = ORACLE_HOME
    env['LD_LIBRARY_PATH'] = LD_LIBRARY_PATH

    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        if should_download_while_dry_run():
            download_cx_oracle()
            download_oracle_driver()
            install_resource(python_sourcecode_package_resource(package_dir=CX_ORACLE_HOME, name='cx_Oracle', version='5.1.2', env=env))
        dry_run_result['oracle-driver'] = action or '-'
        return
    if not action:
        return
    download_cx_oracle()
    download_oracle_driver()
    install_resource(python_sourcecode_package_resource(package_dir=CX_ORACLE_HOME, name='cx_Oracle', version='5.1.2', env=env))
    install_resource(file_resource(path='/etc/ld.so.conf.d/oracle_driver.conf', content=ORACLE_HOME))
    shell_execute('ldconfig')
    if VEIL_ENV_TYPE in ('development', 'test'):
        set_resource_latest_version('veil.backend.database.oracle_driver.oracle_driver_resource', '11.2.0.1')


def download_oracle_driver():
    if os.path.exists(ORACLE_HOME):
        return
    mirror = os.getenv('VEIL_DEPENDENCY_MIRROR')
    if mirror:
        mirror = '{}:8080'.format(mirror)
    else:
        mirror = 'http://dependency-veil.qiniudn.com'
    shell_execute('wget {}/oracle-instantclient11.2-basic-11.2.0.1.0-1.x86_64.zip -O /tmp/oracle-instantclient11.2-basic-11.2.0.1.0-1.x86_64.zip'.format(mirror))
    shell_execute('unzip /tmp/oracle-instantclient11.2-basic-11.2.0.1.0-1.x86_64.zip -d /opt')
    shell_execute('wget {}/oracle-instantclient11.2-sdk-11.2.0.1.0-1.x86_64.zip -O /tmp/oracle-instantclient11.2-sdk-11.2.0.1.0-1.x86_64.zip'.format(mirror))
    shell_execute('unzip /tmp/oracle-instantclient11.2-sdk-11.2.0.1.0-1.x86_64.zip -d /opt')
    shell_execute('ln -s libclntsh.so.11.1 libclntsh.so', cwd=CX_ORACLE_HOME)


def download_cx_oracle():
    if os.path.exists(CX_ORACLE_HOME):
        return
    mirror = os.getenv('VEIL_DEPENDENCY_MIRROR')
    if mirror:
        mirror = '{}:8080'.format(mirror)
    else:
        mirror = 'http://dependency-veil.qiniudn.com'
    shell_execute('wget {}/cx_Oracle-5.1.2.tar.gz -O /tmp/cx_Oracle-5.1.2.tar.gz'.format(mirror))
    shell_execute('tar xvf /tmp/cx_Oracle-5.1.2.tar.gz -C /opt')