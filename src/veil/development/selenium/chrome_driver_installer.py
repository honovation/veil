from __future__ import unicode_literals, print_function, division
import logging
import os
from veil.env_const import VEIL_DEPENDENCY_URL, VEIL_ENV_TYPE
from veil_installer import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)

DEFAULT_VERSION = '2.9'
RESOURCE_KEY = 'veil.development.selenium.chrome_driver_resource'
CHROMEDRIVER_PATH = '/usr/bin/chromedriver'


def get_installed_version():
    if not os.path.exists(CHROMEDRIVER_PATH):
        return None
    return shell_execute('readlink {}'.format(CHROMEDRIVER_PATH), capture=True).rsplit('-', 1)[1].strip()



@atomic_installer
def chrome_driver_resource(version=None):
    version = version or DEFAULT_VERSION
    latest_version = get_resource_latest_version(RESOURCE_KEY)
    installed_version = get_installed_version()
    is_installed = True if installed_version and installed_version == latest_version == version else False
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['chrome_driver'] = '-' if is_installed else 'INSTALL'
        return
    if is_installed:
        return
    url = '{}/chromedriver/{}/chromedriver_linux64.zip'.format(VEIL_DEPENDENCY_URL, version)
    local_path = '/tmp/chromedriver_linux64_{}.zip'.format(version)
    LOGGER.info('installing selenium webdriver for chrome: from %(url)s...', {'url': url})
    shell_execute('wget {} -O {}'.format(url, local_path))
    shell_execute('unzip {} -d /usr/bin'.format(local_path))
    shell_execute('mv {} {}-{}'.format(CHROMEDRIVER_PATH, CHROMEDRIVER_PATH, version))
    shell_execute('ln -sf {}-{} {}'.format(CHROMEDRIVER_PATH, version, CHROMEDRIVER_PATH))
    shell_execute('chown {}:{} {}-{}'.format(os.environ.get('SUDO_UID'), os.environ.get('SUDO_GID'), CHROMEDRIVER_PATH, version))
    if VEIL_ENV_TYPE in ('development', 'test'):
        set_resource_latest_version(RESOURCE_KEY, version)