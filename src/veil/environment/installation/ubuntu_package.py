from __future__ import unicode_literals, print_function, division
from veil.backend.shell import *
from veil.utility.path import *

def install_ubuntu_package(package_name):
    try:
        shell_execute('dpkg -L {}'.format(package_name), capture=True, silent=True)
    except ShellExecutionError, e:
        if 'not installed' in e.output:
            shell_execute('apt-get -y install {}'.format(package_name))


def remove_service_auto_start(service_name, test_file):
    if as_path(test_file).exists():
        shell_execute('service {} stop'.format(service_name))
        shell_execute('update-rc.d -f {} remove'.format(service_name))
