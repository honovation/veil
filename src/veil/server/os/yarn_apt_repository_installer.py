from __future__ import unicode_literals, print_function, division
import logging
from veil_installer import *
from .os_package_repository_installer import install_apt_repository_resource

LOGGER = logging.getLogger(__name__)

APT_REPOSITORY_NAME = 'yarn'


@atomic_installer
def yarn_apt_repository_resource():
    key_url = 'https://dl.yarnpkg.com/debian/pubkey.gpg'
    definition = 'deb https://dl.yarnpkg.com/debian/ stable main'
    install_apt_repository_resource(APT_REPOSITORY_NAME, key_url, definition)
