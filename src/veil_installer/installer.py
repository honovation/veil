from __future__ import unicode_literals, print_function, division
import veil_component
import logging

LOGGER = logging.getLogger()
INSTALLERS = {}
stack = []
installed_resource_codes = set()
installed_installer_providers = set()

def installer(name):
    def register(func):
        register_installer(name, func)
        return func

    return register


def register_installer(name, installer):
    INSTALLERS[name] = installer


def install_resources(dry_run_result, installer_providers, resources):
    installer_providers = list(skip_installed_installer_providers(installer_providers))
    resources = list(skip_installed_resources(resources))
    stack.append((installer_providers, resources))
    if len(stack) > 30:
        for frame in stack:
            print(frame)
        raise Exception('too many levels')
    if installer_providers:
        install_installer_providers(dry_run_result, installer_providers)
    for resource in resources:
        more_installer_providers, more_resources = install_resource(dry_run_result, resource)
        install_resources(dry_run_result, more_installer_providers, more_resources)
    stack.pop()


def install_installer_providers(dry_run_result, installer_providers):
    installer_provider_component_resources = []
    for installer_provider in installer_providers:
        veil_component.scan_component(installer_provider)
        installer_provider_component = veil_component.get_root_component(installer_provider)
        installer_provider_component_resource = ('component', dict(name=installer_provider_component))
        installer_provider_component_resources.append(installer_provider_component_resource)
    install_resources(dry_run_result, [], installer_provider_component_resources)
    for installer_provider in installer_providers:
        try:
            __import__(installer_provider)
            if dry_run_result is not None:
                dry_run_result['@{}'.format(installer_provider)] = '-'
        except:
            if dry_run_result is not None:
                dry_run_result['@{}'.format(installer_provider)] = 'INSTALL'
            else:
                LOGGER.error('failed to load installer provider: {}'.format(installer_provider))
                raise


def install_resource(dry_run_result, resource):
    installer_name, installer_args = resource
    if installer_name not in INSTALLERS:
        if dry_run_result is not None:
            return [], []
        raise Exception('no installer for: {} {}'.format(installer_name, installer_args))
    result = INSTALLERS[installer_name](dry_run_result=dry_run_result, **installer_args)
    if result:
        return result # installer_providers, resources
    else:
        return [], []


def skip_installed_installer_providers(installer_providers):
    for installer_provider in installer_providers:
        if installer_provider not in installed_installer_providers:
            installed_installer_providers.add(installer_provider)
            yield installer_provider


def skip_installed_resources(resources):
    for resource in resources:
        resource_code = to_resource_code(resource)
        if resource_code not in installed_resource_codes:
            installed_resource_codes.add(resource_code)
            yield resource


def to_resource_code(resource):
    if len(resource) != 2:
        raise Exception('invalid resource: {}'.format(resource))
    installer_name, installer_args = resource
    if not isinstance(installer_args, dict):
        raise Exception('invalid resource: {}, {}'.format(installer_name, installer_args))
    resource_code = '{}?{}'.format(installer_name, '&'.join(
        ['{}={}'.format(k, installer_args[k])
         for k in sorted(installer_args.keys())]))
    return resource_code