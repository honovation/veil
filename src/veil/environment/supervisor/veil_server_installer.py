from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment import *
from veil.environment.setting import *
from .program_installer import program_resource

@composite_installer('veil_server')
def install_veil_server(dry_run_result):
    config = get_settings().supervisor
    if VEIL_SERVER in ['development', 'test']:
        resources = [program_resource(p) for p in config.programs.keys()]
    else:
        server = get_current_veil_server()
        resources = [program_resource(p) for p in server.programs]
    resources.append(('supervisor', {}))
    return [], resources
