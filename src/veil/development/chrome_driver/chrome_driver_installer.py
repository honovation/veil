from __future__ import unicode_literals, print_function, division
import os
from veil_installer import *
from veil.backend.shell import *

@installer('chrome_driver')
def install_chrome_driver(dry_run_result):
    is_installed = os.path.exists('/usr/bin/chromedriver')
    if dry_run_result is not None:
        dry_run_result['chrome_driver'] = '-' if is_installed else 'INSTALL'
        return
    if is_installed:
        return
    mirror = os.getenv('VEIL_DEPENDENCY_MIRROR', 'http://chromedriver.googlecode.com/files')
    shell_execute('wget {}/chromedriver_linux64_21.0.1180.4.zip -O /tmp/chromedriver_linux64_21.0.1180.4.zip'.format(mirror))
    shell_execute('unzip /tmp/chromedriver_linux64_21.0.1180.4.zip -d /usr/bin')