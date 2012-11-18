from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment import *

@composite_installer('veil_server')
def install_veil_server():
    veil_server_programs = list_current_veil_server_programs()
    installer_providers = ['veil.environment.supervisor']
    resources = [('supervisor', {'programs': to_supervisor_programs(veil_server_programs)})]
    for program in veil_server_programs.values():
        installer_providers.extend(program.get('installer_providers', []))
        for key, value in program.items():
            if key.endswith('_resource'):
                installer_name = key.replace('_resource', '')
                resources.append((installer_name, value))
    return installer_providers, resources


def to_supervisor_programs(veil_server_programs):
    supervisor_programs = {}
    for program_name, program in veil_server_programs.items():
        supervisor_programs[program_name] = {
            'execute_command': program.execute_command,
            'user': CURRENT_USER
        }
    return supervisor_programs
