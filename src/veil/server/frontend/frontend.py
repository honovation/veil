# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.utility.shell import *
from veil_component import as_path
from veil_installer import *


@atomic_installer
def frontend_static_resource(frontend_root_path):
    frontend_root_path = as_path(frontend_root_path)
    if not frontend_root_path or not (frontend_root_path / 'package.json').exists():
        return
    shell_execute('sudo npm install yarn -g --registry=https://registry.npm.taobao.org', cwd=frontend_root_path)
    shell_execute('yarn install --registry=https://registry.npm.taobao.org', cwd=frontend_root_path)
    shell_execute('yarn run build', cwd=frontend_root_path)
