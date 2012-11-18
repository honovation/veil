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
    for program_name, veil_server_program in veil_server_programs.items():
        supervisor_program = {
            'execute_command': veil_server_program.execute_command,
            'user': CURRENT_USER
        }
        if 'environment_variables' in veil_server_program:
            supervisor_program['environment_variables'] = format_environment_variables(
                veil_server_program.environment_variables)
        supervisor_programs[program_name] = supervisor_program
    return supervisor_programs


def format_environment_variables(environment_variables):
    return ','.join(['{}={}'.format(k, v) for k, v in environment_variables.items()])
