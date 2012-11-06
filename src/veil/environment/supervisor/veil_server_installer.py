from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment import *
from veil.environment.setting import *
from veil.environment.supervisor_setting import supervisor_settings
from .program_installer import program_resource

@installer('veil_server')
def install_veil_server(dry_run_result):
    settings = merge_settings(supervisor_settings(), get_settings(), overrides=True)
    config = settings.supervisor
    if VEIL_SERVER in ['development', 'test']:
        resources = [program_resource(p) for p in config.programs.keys()]
    else:
        server = get_current_veil_server()
        resources = [program_resource(p) for p in server.programs]
    resources.append(('supervisor', {}))
    return [], resources
