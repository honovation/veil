from __future__ import unicode_literals, print_function, division
import pprint

INSTALLERS = {}

def register_installer(name, installer):
    INSTALLERS[name] = installer


def install_resource(is_dry_run, resource):
    if is_dry_run:
        pprint.pprint(list_resource_map(resource))
        return

    installer_name, installer_args = resource
    if installer_name not in INSTALLERS:
        raise Exception('no installer for: {} {}'.format(installer_name, installer_args))
    more_resources = INSTALLERS[installer_name](is_dry_run=False, **installer_args)
    for more_resource in more_resources or []:
        install_resource(False, more_resource)


def list_resource_map(resource):
    installer_name, installer_args = resource
    if installer_name not in INSTALLERS:
        raise Exception('no installer for: {} {}'.format(installer_name, installer_args))
    installer = INSTALLERS[installer_name]
    result = installer(is_dry_run=True, **installer_args)
    if isinstance(result, bool):
        return '-' if result else 'INSTALL'
    resource_map = {}
    for resource in result:
        sub_resource_map = list_resource_map(resource)
        if isinstance(sub_resource_map, dict):
            resource_map.update(sub_resource_map)
        else:
            resource_map[format_resource(resource)] = list_resource_map(resource)
    return resource_map


def format_resource(resource):
    installer_name, installer_args = resource
    return '{}?{}'.format(installer_name, '&'.join(['{}={}'.format(k, v) for k, v in installer_args.items()]))
