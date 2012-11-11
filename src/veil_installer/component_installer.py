from __future__ import unicode_literals, print_function, division
import logging
import os
import veil_component
from .installer import composite_installer

LOGGER = logging.getLogger(__name__)

def component_resource(name):
    return 'component', dict(name=name)

@composite_installer('component')
def install_component(name):
    component_name = name
    module_loader = veil_component.find_module_loader_without_import(component_name)
    if not module_loader:
        raise Exception('component {} not found'.format(name))
    module_path = module_loader.get_filename()
    module_dir = os.path.dirname(module_path)
    installer_path = os.path.join(module_dir, 'INSTALLER')
    installer_providers = []
    resources = []
    veil_component.scan_component(name)
    for dependent_component_name in veil_component.get_dependent_component_names(component_name, includes_children=True):
        resources.append(('component', dict(name=dependent_component_name)))
    if os.path.exists(installer_path):
        try:
            with open(installer_path) as f:
                lines = f.readlines()
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('@'):
                    installer_provider = line[1:]
                    installer_providers.append(installer_provider)
                else:
                    resources.append(parse_resource(line))
        except:
            LOGGER.error('failed to parse: {}'.format(installer_path))
            raise
    return installer_providers, resources


def parse_resource(line):
    if '?' not in line:
        return line, {}
    installer_name, installer_args = line.split('?')
    if not installer_args:
        return installer_name, {}
    installer_args = [arg if '=' in arg else 'name={}'.format(arg) for arg in installer_args.split('&')]
    installer_args = dict([(arg.split('=')[0].strip(), arg.split('=')[1].strip()) for arg in installer_args])
    return installer_name, installer_args