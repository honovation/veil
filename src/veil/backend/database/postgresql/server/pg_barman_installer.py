# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division

from veil.server.os import *
from veil_installer import *


@composite_installer
def pgbarman_resource():
    resources = [
        postgresql_apt_repository_resource(),
        os_package_resource(name='barman')
    ]
    return resources
