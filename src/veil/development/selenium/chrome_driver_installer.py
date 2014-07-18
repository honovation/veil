from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

LOGGER = logging.getLogger(__name__)
CHROMEDRIVER_PATH = as_path('/usr/bin/chromedriver')
RESOURCE_KEY = 'veil.development.selenium.chrome_driver_resource'
RESOURCE_VERSION = '2.10'


def get_installed_version():
    if not CHROMEDRIVER_PATH.exists():
        return None
    if not CHROMEDRIVER_PATH.islink():
        CHROMEDRIVER_PATH.rename('{}.bak'.format(CHROMEDRIVER_PATH))
        return None
    return shell_execute('readlink {}'.format(CHROMEDRIVER_PATH), capture=True).rsplit('-', 1)[1].strip()


@atomic_installer
def chrome_driver_resource():
    installed_version = get_installed_version()
    installed = installed_version == RESOURCE_VERSION
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['chrome_driver'] = '-' if installed else 'INSTALL'
        return
    if installed:
        if VEIL_ENV_TYPE in ('development', 'test') and RESOURCE_VERSION != get_resource_latest_version(RESOURCE_KEY):
            set_resource_latest_version(RESOURCE_KEY, RESOURCE_VERSION)
        return
    url = '{}/chromedriver/{}/chromedriver_linux64.zip'.format(DEPENDENCY_URL, RESOURCE_VERSION)
    LOGGER.info('installing selenium webdriver for chrome: from %(url)s...', {'url': url})
    local_path = DEPENDENCY_DIR / 'chromedriver_linux64_{}.zip'.format(RESOURCE_VERSION)
    if not os.path.exists(local_path):
        shell_execute('wget -c {} -O {}'.format(url, local_path))
    shell_execute('unzip {} -d /usr/bin'.format(local_path))
    shell_execute('mv {} {}-{}'.format(CHROMEDRIVER_PATH, CHROMEDRIVER_PATH, RESOURCE_VERSION))
    shell_execute('chown {}:{} {}-{}'.format(os.environ.get('SUDO_UID'), os.environ.get('SUDO_GID'), CHROMEDRIVER_PATH, RESOURCE_VERSION))
    shell_execute('ln -sf {}-{} {}'.format(CHROMEDRIVER_PATH, RESOURCE_VERSION, CHROMEDRIVER_PATH))
    if VEIL_ENV_TYPE in ('development', 'test'):
        set_resource_latest_version(RESOURCE_KEY, RESOURCE_VERSION)
