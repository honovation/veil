# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from veil.profile.installer import *


@script('upgrade-server')
def upgrade_server(purpose, from_version, to_version):
    install_resource([
        os_package_resource(name='postgresql-{}'.format(to_version)),
        os_service_resource(state='not_installed', name='postgresql'),

    ])


