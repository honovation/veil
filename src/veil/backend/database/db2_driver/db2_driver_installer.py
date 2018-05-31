from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


IBM_DB_HOME = DEPENDENCY_INSTALL_DIR / 'db2-clidriver'
DB2_DRIVER_CONF_PATH = '/etc/ld.so.conf.d/db2-clidriver.conf'
DB2_DRIVER_CONF_CONTENT = '{}/lib'.format(IBM_DB_HOME)
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
        install_resource(os_package_resource(name='libstdc++-6-dev'))
        install_resource(os_package_resource(name='libstdc++-6-pic'))
        install_db2_clidriver()

    install_resource(python_package_resource(name='ibm_db', env=env))


def download_db2_clidriver():
    if os.path.exists(IBM_DB_HOME):
        return
    local_path = DEPENDENCY_DIR / 'db2-clidriver.tar.gz'
    if not os.path.exists(local_path):
        shell_execute('wget -c {}/db2-clidriver.tar.gz -O {}'.format(DEPENDENCY_URL, local_path))
    shell_execute('tar -xvzf {} -C {}'.format(local_path, DEPENDENCY_INSTALL_DIR))


def is_db2_clidriver_installed():
    if not os.path.exists(DB2_DRIVER_CONF_PATH):
        return False
    with open(DB2_DRIVER_CONF_PATH, 'rb') as f:
        return DB2_DRIVER_CONF_CONTENT == f.read()


def install_db2_clidriver():
    if is_db2_clidriver_installed():
        if (VEIL_ENV.is_dev or VEIL_ENV.is_test) and RESOURCE_VERSION != get_resource_latest_version(RESOURCE_KEY):
            set_resource_latest_version(RESOURCE_KEY, RESOURCE_VERSION)
        return
    download_db2_clidriver()
    install_resource(file_resource(path=DB2_DRIVER_CONF_PATH, content=DB2_DRIVER_CONF_CONTENT, owner=CURRENT_USER, group=CURRENT_USER_GROUP))
    shell_execute('ldconfig')
    if VEIL_ENV.is_dev or VEIL_ENV.is_test:
        set_resource_latest_version(RESOURCE_KEY, RESOURCE_VERSION)
