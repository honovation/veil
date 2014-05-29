from __future__ import unicode_literals, print_function, division
from veil.environment import VEIL_DEPENDENCY_URL
from veil.profile.installer import *


IBM_DB_HOME = '/opt/db2-clidriver'
RESOURCE_KEY = 'veil.backend.database.db_driver.db2_driver_resource'
RESOURCE_VERSION = '9.7'


@atomic_installer
def db2_driver_resource():
    env = os.environ.copy()
    env['IBM_DB_HOME'] = IBM_DB_HOME
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        if is_downloading_while_dry_run():
            download_db2_clidriver()
        dry_run_result['db2-driver'] = '-' if is_db2_clidriver_installed() else 'INSTALL'
    else:
        install_db2_clidriver()

    install_resource(python_package_resource(name='ibm-db', env=env))


def download_db2_clidriver():
    if os.path.exists(IBM_DB_HOME):
        return
    shell_execute('wget {}/db2-clidriver.tar.gz -O /tmp/db2-clidriver.tar.gz'.format(VEIL_DEPENDENCY_URL))
    shell_execute('tar xzf /tmp/db2-clidriver.tar.gz -C /opt')


def is_db2_clidriver_installed():
    return os.path.exists('/etc/ld.so.conf.d/db2-clidriver.conf')


def install_db2_clidriver():
    if is_db2_clidriver_installed():
        if VEIL_ENV_TYPE in ('development', 'test') and RESOURCE_VERSION != get_resource_latest_version(RESOURCE_KEY):
            set_resource_latest_version(RESOURCE_KEY, RESOURCE_VERSION)
        return
    download_db2_clidriver()
    install_resource(file_resource(path='/etc/ld.so.conf.d/db2-clidriver.conf', content='/opt/db2-clidriver/lib'))
    shell_execute('ldconfig')
    if VEIL_ENV_TYPE in ('development', 'test'):
        set_resource_latest_version(RESOURCE_KEY, RESOURCE_VERSION)
