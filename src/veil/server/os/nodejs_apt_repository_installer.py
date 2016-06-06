from __future__ import unicode_literals, print_function, division
import logging
from veil_component import CURRENT_OS
from veil_installer import *
from .os_package_repository_installer import install_apt_repository_resource

LOGGER = logging.getLogger(__name__)

APT_REPOSITORY_NAME = 'node_4.x'


@atomic_installer
def nodejs_apt_repository_resource():
    key_url = 'https://deb.nodesource.com/gpgkey/nodesource.gpg.key'
    definition = 'deb https://deb.nodesource.com/{repository_name} {os_codename} main\ndeb-src https://deb.nodesource.com/{repository_name} {os_codename} main'.format(
        repository_name=APT_REPOSITORY_NAME, os_codename=CURRENT_OS.codename)
    install_apt_repository_resource(APT_REPOSITORY_NAME, key_url, definition)
