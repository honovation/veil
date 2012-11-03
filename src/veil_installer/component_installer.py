from __future__ import unicode_literals, print_function, division
import pkgutil
import os
import veil_component

def install_component(dry_run_result, name):
    component_name = name
    module_path = pkgutil.get_loader(component_name).get_filename()
    module_dir = os.path.dirname(module_path)
    installer_path = os.path.join(module_dir, 'INSTALLER')
    installer_providers = []
    resources = []
    veil_component.add_component(component_name)
    for dependent_component_name in veil_component.get_component_map().get(component_name, set()):
        resources.append(('component', dict(name=dependent_component_name)))
    if os.path.exists(installer_path):
        with open(installer_path) as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('@'):
                installer_providers.append(line[1:])
            else:
                resources.append(parse_resource(line))
    return installer_providers, resources


def parse_resource(line):
    installer_name, installer_args = line.split('?')
    installer_args = [arg if '=' in arg else 'name={}'.format(arg) for arg in installer_args.split('&')]
    installer_args = dict([(arg.split('=')[0].strip(), arg.split('=')[1].strip()) for arg in installer_args])
    return installer_name, installer_args