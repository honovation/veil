from __future__ import unicode_literals, print_function, division
from veil_component import CURRENT_OS
from veil_installer import *
from veil.server.os import *


@atomic_installer
def postgresql_apt_repository_resource():
    install_apt_repository_resource('pgdg', 'https://www.postgresql.org/media/keys/ACCC4CF8.asc',
                                    'deb http://apt.postgresql.org/pub/repos/apt/{}-pgdg main'.format(CURRENT_OS.codename))
