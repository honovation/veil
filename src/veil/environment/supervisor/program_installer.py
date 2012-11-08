from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment.setting import *

def program_resource(name):
    return 'program', dict(name=name)


@installer('program')
def install_program(dry_run_result, name):
    config = get_settings().supervisor
    return config.programs[name].get('installer_providers', []), config.programs[name].get('resources', [])
