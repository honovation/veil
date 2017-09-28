# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

from veil.environment import CURRENT_USER
from veil.utility.shell import *
from veil_component import as_path
from veil_installer import *


@atomic_installer
def frontend_static_resource(frontend_root_path):
    frontend_root_path = as_path(frontend_root_path)
    if not frontend_root_path or not (frontend_root_path / 'package.json').exists():
        return
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['frontend_static_resource'] = 'INSTALL'
        return
    shell_execute('sudo npm install yarn -g --registry=https://registry.npm.taobao.org', cwd=frontend_root_path)
    shell_execute('sudo -u {} yarn install --registry=https://registry.npm.taobao.org'.format(CURRENT_USER), cwd=frontend_root_path)
    shell_execute('sudo -u {} yarn run build'.format(CURRENT_USER), cwd=frontend_root_path)
