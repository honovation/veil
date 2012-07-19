from __future__ import unicode_literals, print_function, division
from sandal.shell import *
from sandal.path import *

def install_ubuntu_package(package_name):
    if shell_execute('dpkg -L {}'.format(package_name), silent=True).returncode:
        shell_execute('apt-get -y install {}'.format(package_name))


def remove_service_auto_start(service_name, test_file):
    if path(test_file).exists():
        shell_execute('service {} stop'.format(service_name))
        shell_execute('update-rc.d -f {} remove'.format(service_name))