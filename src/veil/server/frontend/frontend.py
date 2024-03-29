# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

import logging
from veil.utility.shell import *
from veil_component import as_path
from veil_installer import *


LOGGER = logging.getLogger(__name__)


@atomic_installer
def frontend_static_resource(frontend_root_path):
    frontend_root_path = as_path(frontend_root_path)
    if not frontend_root_path.exists():
        raise Exception('No such directory: {}'.format(frontend_root_path))
    package_desc_file_path = frontend_root_path / 'package.json'
    if not package_desc_file_path.exists():
        raise Exception('No package.json file in: {}'.format(frontend_root_path))

    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['frontend_static_resource'] = 'INSTALL'
        return

    shell_execute('sudo npm install yarn -g', cwd=frontend_root_path)

    node_modules_path = frontend_root_path / 'node_modules'
    if not node_modules_path.exists():
        LOGGER.info('node modules path does not exist, install')
        shell_execute('yarn', cwd=frontend_root_path)

    shell_execute('yarn install', cwd=frontend_root_path)
    shell_execute('yarn run build', cwd=frontend_root_path)
