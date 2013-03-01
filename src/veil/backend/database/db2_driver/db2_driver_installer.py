from __future__ import unicode_literals, print_function, division
import os
from veil.profile.installer import *

@atomic_installer
def db2_driver_resource():
    installed_version = get_python_package_installed_version('ibm-db')
    action = None if installed_version else 'INSTALL'
    if UPGRADE_MODE_LATEST == get_upgrade_mode():
        action = 'UPGRADE'
    elif UPGRADE_MODE_FAST == get_upgrade_mode():
        latest_version = get_resource_latest_version('veil.backend.database.db2_driver.db2_driver_resource')
        action = None if latest_version == installed_version else 'UPGRADE'
    elif UPGRADE_MODE_NO == get_upgrade_mode():
        pass
    else:
        raise NotImplementedError()
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['db2-driver'] = action or '-'
        return
    if not action:
        return
    download_db2_driver()
    env = os.environ.copy()
    env['IBM_DB_HOME'] = '/opt/db2-clidriver'
    install_resource(python_package_resource(name='ibm-db', env=env))
    install_resource(file_resource(path='/etc/ld.so.conf.d/db2-clidriver.conf', content='/opt/db2-clidriver/lib'))
    shell_execute('ldconfig')
    package_version = get_python_package_installed_version('ibm-db', from_cache=False)
    set_resource_latest_version('veil.backend.database.db2_driver.db2_driver_resource', package_version)


def download_db2_driver():
    if os.path.exists('/opt/db2-clidriver'):
        return
    mirror = os.getenv('VEIL_DEPENDENCY_MIRROR')
    if mirror:
        mirror = '{}:8080'.format(mirror)
    else:
        mirror = 'http://dependency-veil.googlecode.com/svn/trunk'
    shell_execute('wget {}/db2-clidriver.tar.gz -O /tmp/db2-clidriver.tar.gz'.format(mirror))
    shell_execute('tar xzf /tmp/db2-clidriver.tar.gz -C /opt')