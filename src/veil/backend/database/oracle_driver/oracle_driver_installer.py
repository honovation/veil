# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


ORACLE_HOME = '/opt/instantclient_11_2'
CX_ORACLE_HOME = '/opt/cx_Oracle-5.1.2'
RESOURCE_KEY = 'veil.backend.database.oracle_driver.oracle_driver_resource'
RESOURCE_VERSION = '11.2.0.1'


@atomic_installer
def oracle_driver_resource():
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        if is_downloading_while_dry_run():
            download_oracle_instantclient()
            download_cx_oracle()
        dry_run_result['oracle-driver'] = '-' if is_oracle_instantclient_installed() else 'INSTALL'
        dry_run_result['python_sourcecode_package?cx_Oracle'] = '-' if is_cx_oracle_installed() else 'INSTALL'
        return
    env = os.environ.copy()
    install_oracle_instantclient(env)
    install_cx_oracle(env)


def download_oracle_instantclient():
    if os.path.exists(ORACLE_HOME):
        return
    shell_execute('wget {}/oracle-instantclient11.2-basic-11.2.0.1.0-1.x86_64.zip -O /tmp/oracle-instantclient11.2-basic-11.2.0.1.0-1.x86_64.zip'.format(VEIL_DEPENDENCY_URL))
    shell_execute('unzip /tmp/oracle-instantclient11.2-basic-11.2.0.1.0-1.x86_64.zip -d /opt')
    shell_execute('wget {}/oracle-instantclient11.2-sdk-11.2.0.1.0-1.x86_64.zip -O /tmp/oracle-instantclient11.2-sdk-11.2.0.1.0-1.x86_64.zip'.format(VEIL_DEPENDENCY_URL))
    shell_execute('unzip /tmp/oracle-instantclient11.2-sdk-11.2.0.1.0-1.x86_64.zip -d /opt')


def is_oracle_instantclient_installed():
    return os.path.exists('/etc/ld.so.conf.d/oracle_driver.conf')


def install_oracle_instantclient(env):
    if is_oracle_instantclient_installed():
        if VEIL_ENV_TYPE in ('development', 'test') and RESOURCE_VERSION != get_resource_latest_version(RESOURCE_KEY):
            set_resource_latest_version(RESOURCE_KEY, RESOURCE_VERSION)
        return
    download_oracle_instantclient()
    shell_execute('ln -s libclntsh.so.11.1 libclntsh.so', cwd=ORACLE_HOME)
    install_resource(file_resource(path='/etc/ld.so.conf.d/oracle_driver.conf', content=ORACLE_HOME))
    env['LD_LIBRARY_PATH'] = '{}:{}'.format(env.get('LD_LIBRARY_PATH', ''), ORACLE_HOME)
    shell_execute('ldconfig')
    if VEIL_ENV_TYPE in ('development', 'test'):
        set_resource_latest_version(RESOURCE_KEY, RESOURCE_VERSION)


def download_cx_oracle():
    if os.path.exists(CX_ORACLE_HOME):
        return
    shell_execute('wget {}/cx_Oracle-5.1.2.tar.gz -O /tmp/cx_Oracle-5.1.2.tar.gz'.format(VEIL_DEPENDENCY_URL))
    shell_execute('tar xvf /tmp/cx_Oracle-5.1.2.tar.gz -C /opt')


def is_cx_oracle_installed():
    return get_python_package_installed_version('cx-Oracle')


def install_cx_oracle(env):
    download_cx_oracle()
    env['ORACLE_HOME'] = ORACLE_HOME
    install_resource(python_sourcecode_package_resource(package_dir=CX_ORACLE_HOME, name='cx_Oracle', version='5.1.2', env=env))
