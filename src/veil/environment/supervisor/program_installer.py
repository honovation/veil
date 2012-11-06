from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment.setting import *
from veil.environment.supervisor_setting import supervisor_settings

@installer('program')
def install_program(dry_run_result, name):
    settings = merge_settings(supervisor_settings(), get_settings(), overrides=True)
    config = settings.supervisor
    return config.programs[name].get('installer_providers', []), config.programs[name].get('resources', [])
