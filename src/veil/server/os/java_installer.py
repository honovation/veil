from __future__ import unicode_literals, print_function, division
from veil_installer import *
from .os_package_repository_installer import os_ppa_repository_resource
from .os_package_installer import os_package_resource


@composite_installer
def oracle_java_resource():
    installer_package_name = 'oracle-java8-installer'
    accept_license = 'echo {} shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections'.format(installer_package_name)
    resources = [
        os_ppa_repository_resource(name='webupd8team/java'),
        os_package_resource(name=installer_package_name, cmd_run_before_install=accept_license)
    ]
    return resources
