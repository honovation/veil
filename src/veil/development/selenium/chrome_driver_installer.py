from __future__ import unicode_literals, print_function, division
import logging
import os
from veil.env_const import VEIL_DEPENDENCY_URL
from veil_installer import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)


@atomic_installer
def chrome_driver_resource():
    is_installed = os.path.exists('/usr/bin/chromedriver')
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['chrome_driver'] = '-' if is_installed else 'INSTALL'
        return
    if is_installed:
        return
    version = '2.6'
    url = '{}/chromedriver/{}/chromedriver_linux64.zip'.format(VEIL_DEPENDENCY_URL, version)
    local_path = '/tmp/chromedriver_linux64_{}.zip'.format(version)
    LOGGER.info('installing selenium webdriver for chrome: from %(url)s...', {'url': url})
    shell_execute('wget {} -O {}'.format(url, local_path))
    shell_execute('unzip {} -d /usr/bin'.format(local_path))
