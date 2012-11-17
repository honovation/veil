from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment import *

@composite_installer('veil_server')
def install_veil_server():
    installer_providers = []
    resources = []
    for program in list_current_veil_server_programs().values():
        installer_providers.extend(program.get('installer_providers', []))
        for key, value in program.items():
            if key.endswith('_resource'):
                installer_name = key.replace('_resource', '')
                resources.append((installer_name, value))
    return installer_providers, resources
