# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *


@composite_installer
def tasktiger_admin_resource(host, port, broker_host, broker_port, broker_db=0):
    config = {'host': host, 'port': port, 'broker_host': broker_host, 'broker_port': broker_port, 'broker_db': broker_db}
    return [
        python_package_resource(name='tasktiger-admin'),
        file_resource(path=VEIL_ETC_DIR / 'tasktiger-admin.cfg', content=render_config('tasktiger-admin.cfg.j2', **config))
    ]
